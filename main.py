from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr, BaseModel
from database import test_connection, user_collection, rule_collection
from models import UserModel, Token, AdRuleModel
from auth import get_password_hash, verify_password, create_access_token, get_current_user
from contextlib import asynccontextmanager
from deployment import get_cloud_adapter  # Added the deployment engine import

# Lifespan context manager to handle startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up AdMesh API...")
    await test_connection()
    yield
    print("Shutting down AdMesh API...")

app = FastAPI(title="AdMesh Control Plane API", lifespan=lifespan)

# --- CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your React app to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AdMesh API is running"}

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: dict):
    # 1. Check if user already exists in MongoDB
    existing_user = await user_collection.find_one({"email": user_data.get("email")})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Hash the password
    hashed_pw = get_password_hash(user_data.get("password"))

    # 3. Validate and construct the user document using our Pydantic model
    try:
        new_user = UserModel(
            email=user_data.get("email"),
            hashed_password=hashed_pw,
            role=user_data.get("role"),
            # Seed mock integrations so you can instantly test the deployment route
            integrations={
                "vercel": {"oauth_token": "ver_xyz123"},
                "aws": {"iam_role_arn": "arn:aws:iam::123456789:role/AdMeshAccess"},
                "github": {"github_app_id": "gh_app_9876"}
            }
        )
    except ValueError as e:
         raise HTTPException(status_code=422, detail=str(e))

    # 4. Insert into MongoDB
    result = await user_collection.insert_one(new_user.model_dump())

    return {
        "message": "User successfully registered",
        "user_id": str(result.inserted_id),
        "role": new_user.role
    }

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # 1. Find the user by email (form_data.username)
    user = await user_collection.find_one({"email": form_data.username})
    
    # 2. Check if user exists and password matches
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Mint the JWT token containing their user ID and role
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "role": user["role"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_ad_rule(rule_data: AdRuleModel, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "advertiser":
        raise HTTPException(status_code=403, detail="Only advertisers can create rules")
        
    # Ensure the rule is owned by the user creating it
    rule_dict = rule_data.model_dump()
    rule_dict["owner_id"] = str(current_user["_id"])
    
    result = await rule_collection.insert_one(rule_dict)
    return {"message": "Rule created", "rule_id": str(result.inserted_id)}

@app.get("/deliver")
async def deliver_ad(zone: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "publisher":
        raise HTTPException(status_code=403, detail="Only publishers can fetch ads")
        
    blacklisted_categories = current_user.get("blacklisted_categories", [])
    
    query = {
        "is_active": True,
        "zone": zone,
        "ad_categories": {"$nin": blacklisted_categories}
    }
    
    rule = await rule_collection.find_one(query)
    
    if not rule:
        return {"status": "no_fill", "htmlContent": ""}
        
    return {
        "status": "success",
        "zone": rule.get("zone"),
        "htmlContent": rule.get("html_payload")
    }

# --- NEW OMNI-CHANNEL DEPLOYMENT ROUTE ---
class DeployPayload(BaseModel):
    provider: str
    target_repo: str

@app.post("/deploy")
async def trigger_deployment(payload: DeployPayload, current_user: dict = Depends(get_current_user)):
    """
    Routes the deployment request to the correct cloud adapter (Vercel, AWS, GitHub).
    """
    if current_user.get("role") != "publisher":
        raise HTTPException(status_code=403, detail="Only publishers can trigger cloud deployments.")
        
    provider = payload.provider.lower()
    
    # 1. Retrieve the user's stored integration credentials
    credentials = current_user.get("integrations", {}).get(provider)
    
    if not credentials:
        # Fallback for testing purposes if user hasn't explicitly linked an account yet
        credentials = {"token": "demo_fallback_credential"}
        
    # 2. Get the specific cloud logic from deployment.py
    adapter = get_cloud_adapter(provider)
    if not adapter:
        raise HTTPException(status_code=400, detail=f"Unsupported cloud provider: {provider}")
        
    # 3. Execute the deployment
    result = await adapter.inject_admesh(
        repository_url=payload.target_repo, 
        credentials=credentials, 
        payload={"ad_zone": "sidebar"}
    )
    
    return result