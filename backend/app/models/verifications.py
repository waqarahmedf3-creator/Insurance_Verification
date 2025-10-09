"""
Verifications database model
"""

from sqlalchemy import Column, String, DateTime, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base

class SourceType(str, enum.Enum):
    """Source type enumeration"""
    CACHE = "cache"
    PROVIDER = "provider"

class Verification(Base):
    """Verification model for storing verification history"""
    
    __tablename__ = "verifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)
    member_key_hash = Column(Text, nullable=False, index=True)  # Hashed member identification
    normalized_request = Column(JSONB, nullable=False)  # Structured request data
    provider_response = Column(JSONB, nullable=False)  # Provider API response
    source = Column(Enum(SourceType), nullable=False, default=SourceType.PROVIDER)
    verified_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    provider = relationship("Provider", back_populates="verifications")
    
    def __repr__(self):
        return f"<Verification(id={self.id}, request_id={self.request_id}, source={self.source})>"
