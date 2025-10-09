"""
Policies database model
"""

from sqlalchemy import Column, String, DateTime, Enum, Text, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base

class CoverageStatus(str, enum.Enum):
    """Coverage status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    PENDING = "pending"

class PolicyType(str, enum.Enum):
    """Policy type enumeration"""
    HEALTH = "health"
    LIFE = "life"
    AUTO = "auto"
    HOME = "home"

class SourceType(str, enum.Enum):
    """Source type enumeration"""
    PROVIDER = "provider"
    CACHE = "cache"
    MANUAL = "manual"

class Policy(Base):
    """Enhanced Policy model for comprehensive policy management"""
    
    __tablename__ = "policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic identification
    provider = Column(String(100), nullable=False, index=True)
    member_id = Column(String(6), nullable=False, index=True)
    policy_number = Column(String(100), nullable=True, index=True)
    
    # Personal information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False, index=True)
    dob = Column(DateTime(timezone=True), nullable=True)  # Date of birth
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Address information
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state_prov = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    
    # Policy details
    policy_type = Column(Enum(PolicyType), nullable=False, default=PolicyType.HEALTH)
    coverage_status = Column(Enum(CoverageStatus), nullable=False, default=CoverageStatus.PENDING)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    coverage_amount = Column(Float, nullable=True)
    premium_amount = Column(Float, nullable=True)
    
    # System fields
    source = Column(Enum(SourceType), nullable=False, default=SourceType.MANUAL)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Policy(id={self.id}, policy_number={self.policy_number}, status={self.coverage_status})>"
