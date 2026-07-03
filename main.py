from fastapi import FastAPI, HTTPException, status, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from datetime import datetime, timezone
from database import test_connection, user_collection, rule_collection, redis_client
from models import UserModel, Token, AdRuleModel
from auth import get_password_hash, verify_password, create_access_token, get_current_user
from contextlib import asynccontextmanager
from deployment import get_cloud_adapter

# --- TELEMETRY HELPER ---
async def log_event_to_redis(event_type: str, zone: str, publisher_id: str):
    """Pushes a tracking event into a high-speed Redis Stream."""
    timestamp = datetime.now(timezone.utc).isoformat()
    event_data = {"event": event_type, "zone": zone, "timestamp": timestamp}
    await redis_client.xadd(f"telemetry:{publisher_id}", event_data)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up AdMesh API...")
    await test_connection()
    yield
    print("Shutting down AdMesh API...")

app = FastAPI(title="AdMesh Control Plane API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AdMesh API is running"}

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: dict):
    existing_user = await user_collection.find_one({"email": user_data.get("email")})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user_data.get("password"))
    try:
        new_user = UserModel(
            email=user_data.get("email"),
            hashed_password=hashed_pw,
            role=user_data.get("role"),
            integrations={} 
        )
    except ValueError as e:
         raise HTTPException(status_code=422, detail=str(e))

    result = await user_collection.insert_one(new_user.model_dump())
    return {"message": "User successfully registered", "user_id": str(result.inserted_id), "role": new_user.role}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await user_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "role": user["role"]}
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user["role"]
    }

# --- CORE MVP ENDPOINTS ---

@app.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_ad_rule(rule_data: AdRuleModel, current_user: dict = Depends(get_current_user)):
    """Deploys a payload into the network."""
    if current_user.get("role") != "advertiser":
        raise HTTPException(status_code=403, detail="Only advertisers can create rules")
        
    rule_dict = rule_data.model_dump()
    rule_dict["owner_id"] = str(current_user["_id"])
    
    # 1. Save to MongoDB for persistent storage
    result = await rule_collection.insert_one(rule_dict)
    
    # 2. Push directly to the high-speed Redis Edge Cache
    cache_key = f"active_ad:{rule_data.zone}"
    await redis_client.set(cache_key, rule_data.html_payload)
    
    return {"message": "Payload injected into network cache", "rule_id": str(result.inserted_id)}

@app.get("/deliver")
async def deliver_ad(zone: str, publisher_id: str = "guest", background_tasks: BackgroundTasks = None):
    """Fetches the active payload and logs telemetry."""
    cache_key = f"active_ad:{zone}"
    cached_html = await redis_client.get(cache_key)
    
    # Fire telemetry event in the background (no latency hit for the user)
    if background_tasks:
        background_tasks.add_task(log_event_to_redis, "impression", zone, publisher_id)
        
    if cached_html:
        return {"status": "success", "zone": zone, "htmlContent": cached_html, "source": "redis_edge"}
        
    return {"status": "no_fill", "htmlContent": ""}

@app.get("/track")
async def track_event(zone: str, event: str, publisher_id: str, background_tasks: BackgroundTasks):
    """Silent tracking pixel for impressions and clicks."""
    if event not in ["impression", "click"]:
        raise HTTPException(status_code=400, detail="Invalid event type")
        
    background_tasks.add_task(log_event_to_redis, event, zone, publisher_id)
    return {"status": "tracked"}

@app.get("/marketplace")
async def get_marketplace_inventory(current_user: dict = Depends(get_current_user)):
    """
    Dynamically fetches all integrated publisher repositories from the database.
    Only users with the 'advertiser' role are permitted access.
    """
    # 1. Enforce Role-Based Access Control (RBAC)
    if current_user.get("role") != "advertiser":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only advertisers can access the marketplace."
        )
    
    # 2. Query users who have successfully registered integration hooks
    # We look for documents where the 'integrations' field is present and not empty
    cursor = user_collection.find({"integrations": {"$ne": {}}})
    integrated_publishers = await cursor.to_list(length=100)
    
    inventory = []
    
    # 3. Format the dynamic inventory for the frontend
    for pub in integrated_publishers:
        integrations = pub.get("integrations", {})
        
        # Iterate through provider integrations (e.g., github)
        for provider, details in integrations.items():
            inventory.append({
                "id": str(pub["_id"]),
                "site": details.get("repo_name", "Integrated Repository"),
                "zone": "sidebar",  # Default zone for the MVP
                "traffic": "Live",
                "framework": "Detected",
                "is_dynamic": True
            })
    
    return {"inventory": inventory}
# --- CLOUD DEPLOYMENT ENDPOINTS ---

class DeployPayload(BaseModel):
    provider: str
    target_repo: str
    github_token: Optional[str] = None

@app.post("/deploy")
async def trigger_deployment(payload: DeployPayload, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "publisher":
        raise HTTPException(status_code=403, detail="Only publishers can trigger cloud deployments.")
        
    provider = payload.provider.lower()
    credentials = current_user.get("integrations", {}).get(provider, {})
    
    if payload.github_token:
        credentials["github_token"] = payload.github_token
        
    adapter = get_cloud_adapter(provider)
    if not adapter:
        raise HTTPException(status_code=400, detail=f"Unsupported cloud provider: {provider}")
        
    result = await adapter.inject_admesh(
        repository_url=payload.target_repo, 
        credentials=credentials, 
        payload={"ad_zone": "sidebar"}
    )
    return result

@app.post("/undeploy")
async def trigger_unlink(payload: DeployPayload, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "publisher":
        raise HTTPException(status_code=403, detail="Only publishers can unlink deployments.")
        
    provider = payload.provider.lower()
    credentials = current_user.get("integrations", {}).get(provider, {})
    
    if payload.github_token:
        credentials["github_token"] = payload.github_token
        
    adapter = get_cloud_adapter(provider)
    if not adapter:
        raise HTTPException(status_code=400, detail=f"Unsupported cloud provider: {provider}")
        
    result = await adapter.remove_admesh(
        repository_url=payload.target_repo, 
        credentials=credentials, 
        payload={"ad_zone": "sidebar"}
    )
    
    await user_collection.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$unset": {f"integrations.{provider}": ""}}
    )
    
    await redis_client.delete(f"active_ad:sidebar")
    
    result["message"] = "Integration severed. Cache flushed and repository cleanup queued."
    return result