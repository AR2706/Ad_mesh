from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone

class UserModel(BaseModel):
    """Schema for Publishers and Advertisers"""
    email: EmailStr
    hashed_password: str
    role: str = Field(..., description="Must be 'publisher' or 'advertiser'")
    is_active: bool = True
    
    # Optional: For publishers storing their deployment credentials securely
    cloud_token: Optional[str] = None 
    
    # Optional: For publishers avoiding conflict of interest
    blacklisted_categories: List[str] = [] 
    
    # NEW: Securely stores OAuth tokens and IAM roles per user for omni-channel deployment
    integrations: Dict[str, dict] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AdRuleModel(BaseModel):
    """Schema for the Advertiser's payload and AI targeting rules"""
    owner_id: Optional[str] = None  # Make this optional so the backend can set it securely
    target_framework: str = "generic" 
    zone: str 
    html_payload: str
    ad_categories: List[str] 
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Token(BaseModel):
    """Schema for the JWT Auth Token response"""
    access_token: str
    token_type: str
    role: Optional[str] = None