"""
Pydantic schemas for authentication
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Schema for user creation"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password", min_length=8)
    full_name: str = Field(..., description="Full name", min_length=1)

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class Token(BaseModel):
    """Schema for authentication token"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")

class TokenData(BaseModel):
    """Schema for token payload data"""
    user_id: Optional[str] = None
    email: Optional[str] = None

class UserResponse(BaseModel):
    """Schema for user information response"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: str = Field(..., description="Full name")
    is_active: bool = Field(..., description="User active status")
    created_at: datetime = Field(..., description="Account creation date")
    
    class Config:
        from_attributes = True
