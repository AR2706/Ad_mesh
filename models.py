from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone

class UserModel(BaseModel):
    email: EmailStr
    hashed_password: str
    role: str = Field(..., description="Must be 'publisher' or 'advertiser'")
    is_active: bool = True
    cloud_token: Optional[str] = None
    blacklisted_categories: List[str] = []
    integrations: Dict[str, dict] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AdRuleModel(BaseModel):
    owner_id: Optional[str] = None
    target_framework: str = "generic"
    zone: str
    html_payload: str
    ad_categories: List[str]
    is_active: bool = True
    geo_targets: List[str] = []
    allowed_days: List[int] = [0, 1, 2, 3, 4, 5, 6]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Token(BaseModel):
    access_token: str
    token_type: str
    role: Optional[str] = None