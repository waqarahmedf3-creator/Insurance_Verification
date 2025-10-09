"""
Pydantic schemas for verification endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class CoverageStatus(str, Enum):
    """Coverage status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"

class SourceType(str, Enum):
    """Source type enumeration"""
    CACHE = "cache"
    PROVIDER = "provider"

class VerificationRequest(BaseModel):
    """Request schema for insurance verification"""
    provider: str = Field(..., description="Insurance provider name")
    member_id: str = Field(..., description="Member ID", min_length=1)
    dob: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    last_name: str = Field(..., description="Last name", min_length=1)
    
    @validator('dob')
    def validate_dob(cls, v):
        """Validate date of birth format"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date of birth must be in YYYY-MM-DD format')

class VerificationResponse(BaseModel):
    """Response schema for insurance verification"""
    request_id: uuid.UUID = Field(..., description="Unique request identifier")
    status: str = Field(..., description="Verification status")
    verified_at: datetime = Field(..., description="Verification timestamp")
    source: SourceType = Field(..., description="Data source (cache or provider)")
    provider_response: Dict[str, Any] = Field(..., description="Provider API response")
    
    class Config:
        from_attributes = True

class PolicyInfoRequest(BaseModel):
    """Request schema for policy information queries"""
    member_id: str = Field(..., description="Member ID", min_length=1)
    dob: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    last_name: str = Field(..., description="Last name", min_length=1)
    
    @validator('dob')
    def validate_dob(cls, v):
        """Validate date of birth format"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date of birth must be in YYYY-MM-DD format')

class PolicyInfoResponse(BaseModel):
    """Response schema for policy information"""
    policy_number: Optional[str] = Field(None, description="Policy number")
    coverage_status: Optional[CoverageStatus] = Field(None, description="Coverage status")
    expiry_date: Optional[datetime] = Field(None, description="Policy expiry date")
    source: SourceType = Field(..., description="Data source (cache or provider)")
    verified_at: datetime = Field(..., description="Verification timestamp")
    
    class Config:
        from_attributes = True

class VerificationDetailsResponse(BaseModel):
    """Response schema for detailed verification information"""
    id: uuid.UUID
    request_id: uuid.UUID
    provider_name: str
    member_key_hash: str
    normalized_request: Dict[str, Any]
    provider_response: Dict[str, Any]
    source: SourceType
    verified_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
