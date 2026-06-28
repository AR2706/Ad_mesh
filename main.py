from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from database import test_connection, user_collection, rule_collection, redis_client
from models import UserModel, Token, AdRuleModel
from auth import get_password_hash, verify_password, create_access_token, get_current_user
from contextlib import asynccontextmanager
from deployment import get_cloud_adapter

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
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_ad_rule(rule_data: AdRuleModel, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "advertiser":
        raise HTTPException(status_code=403, detail="Only advertisers can create rules")
    rule_dict = rule_data.model_dump()
    rule_dict["owner_id"] = str(current_user["_id"])
    result = await rule_collection.insert_one(rule_dict)
    await redis_client.delete(f"ad_cache:*:{rule_data.zone}")
    return {"message": "Rule created and cache flushed", "rule_id": str(result.inserted_id)}

@app.get("/deliver")
async def deliver_ad(zone: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "publisher":
        raise HTTPException(status_code=403, detail="Only publishers can fetch ads")
    publisher_id = str(current_user["_id"])
    cache_key = f"ad_cache:{publisher_id}:{zone}"
    
    cached_ad = await redis_client.get(cache_key)
    if cached_ad:
        return {"status": "success", "zone": zone, "htmlContent": cached_ad, "source": "redis_edge"}
        
    blacklisted_categories = current_user.get("blacklisted_categories", [])
    query = {
        "is_active": True,
        "zone": zone,
        "ad_categories": {"$nin": blacklisted_categories}
    }
    rule = await rule_collection.find_one(query)
    
    if not rule:
        return {"status": "no_fill", "htmlContent": ""}
        
    html_payload = rule.get("html_payload")
    await redis_client.setex(cache_key, 300, html_payload)
    return {"status": "success", "zone": rule.get("zone"), "htmlContent": html_payload, "source": "mongodb_origin"}

# --- UPDATED PAYLOAD TO ACCEPT TOKEN ---
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
    
    # Override database credentials with the ones provided in the UI
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
    
    publisher_id = current_user["_id"]
    await redis_client.delete(f"ad_cache:{publisher_id}:sidebar")
    
    result["message"] = "Integration severed. Cache flushed and repository cleanup queued."
    return result