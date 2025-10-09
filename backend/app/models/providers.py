"""
Providers database model
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class Provider(Base):
    """Provider model for storing external insurance provider metadata"""
    
    __tablename__ = "providers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(200), nullable=False)
    api_endpoint = Column(Text, nullable=False)
    api_key = Column(Text, nullable=True)  # Encrypted API key
    is_active = Column(Boolean, nullable=False, default=True)
    rate_limit_per_minute = Column(Integer, nullable=True, default=60)
    timeout_seconds = Column(Integer, nullable=True, default=30)
    configuration = Column(JSONB, nullable=True)  # Provider-specific configuration
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    verifications = relationship("Verification", back_populates="provider")
    
    def __repr__(self):
        return f"<Provider(id={self.id}, name={self.name}, active={self.is_active})>"
