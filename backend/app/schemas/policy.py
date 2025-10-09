"""
Pydantic schemas for policy management endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid

class PolicyType(str, Enum):
    """Policy type enumeration"""
    HEALTH = "health"
    LIFE = "life"
    AUTO = "auto"
    HOME = "home"

class PolicyStatus(str, Enum):
    """Policy status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    PENDING = "pending"

class PolicyCreateRequest(BaseModel):
    """Request schema for creating a new policy"""
    provider: str = Field(..., description="Insurance provider name")
    member_id: str = Field(..., description="Member ID", min_length=1, max_length=6)
    first_name: Optional[str] = Field(None, description="First name")
    last_name: str = Field(..., description="Last name", min_length=1)
    dob: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state_prov: Optional[str] = Field(None, description="State or province")
    zip_code: Optional[str] = Field(None, description="ZIP or postal code")
    policy_type: PolicyType = Field(..., description="Type of policy")
    policy_number: Optional[str] = Field(None, description="Policy number")
    coverage_status: PolicyStatus = Field(..., description="Policy status")
    expiry_date: Optional[str] = Field(None, description="Policy expiry date (YYYY-MM-DD)")
    coverage_amount: Optional[float] = Field(None, description="Coverage amount")
    premium_amount: Optional[float] = Field(None, description="Premium amount")
    
    @validator('dob')
    def validate_dob(cls, v):
        """Validate date of birth format"""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError('Date of birth must be in YYYY-MM-DD format')
        return v
    
    @validator('expiry_date')
    def validate_expiry_date(cls, v):
        """Validate expiry date format"""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError('Expiry date must be in YYYY-MM-DD format')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format"""
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

class PolicyUpdateRequest(BaseModel):
    """Request schema for updating a policy"""
    provider: Optional[str] = Field(None, description="Insurance provider name")
    member_id: Optional[str] = Field(None, description="Member ID", min_length=1, max_length=6)
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name", min_length=1)
    dob: Optional[str] = Field(None, description="Date of birth (YYYY-MM-DD)")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state_prov: Optional[str] = Field(None, description="State or province")
    zip_code: Optional[str] = Field(None, description="ZIP or postal code")
    policy_type: Optional[PolicyType] = Field(None, description="Type of policy")
    policy_number: Optional[str] = Field(None, description="Policy number")
    coverage_status: Optional[PolicyStatus] = Field(None, description="Policy status")
    expiry_date: Optional[str] = Field(None, description="Policy expiry date (YYYY-MM-DD)")
    coverage_amount: Optional[float] = Field(None, description="Coverage amount")
    premium_amount: Optional[float] = Field(None, description="Premium amount")
    
    @validator('dob')
    def validate_dob(cls, v):
        """Validate date of birth format"""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError('Date of birth must be in YYYY-MM-DD format')
        return v
    
    @validator('expiry_date')
    def validate_expiry_date(cls, v):
        """Validate expiry date format"""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError('Expiry date must be in YYYY-MM-DD format')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format"""
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

class PolicyResponse(BaseModel):
    """Response schema for policy"""
    id: uuid.UUID = Field(..., description="Policy ID")
    provider: str = Field(..., description="Insurance provider name")
    member_id: str = Field(..., description="Member ID")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: str = Field(..., description="Last name")
    dob: str = Field(..., description="Date of birth")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state_prov: Optional[str] = Field(None, description="State or province")
    zip_code: Optional[str] = Field(None, description="ZIP or postal code")
    policy_type: PolicyType = Field(..., description="Type of policy")
    policy_number: Optional[str] = Field(None, description="Policy number")
    coverage_status: PolicyStatus = Field(..., description="Policy status")
    expiry_date: Optional[datetime] = Field(None, description="Policy expiry date")
    coverage_amount: Optional[float] = Field(None, description="Coverage amount")
    premium_amount: Optional[float] = Field(None, description="Premium amount")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True

class PolicyListResponse(BaseModel):
    """Response schema for policy list"""
    policies: List[PolicyResponse] = Field(..., description="List of policies")
    total: int = Field(..., description="Total number of policies")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(10, description="Page size")
    
    class Config:
        from_attributes = True