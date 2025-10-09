"""
Verification service for handling insurance verification logic
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, Optional
import uuid
import structlog
from datetime import datetime

from app.models.verifications import Verification
from app.models.providers import Provider
from app.core.redis_client import RedisClient
from app.services.provider_service import ProviderService

logger = structlog.get_logger()

class VerificationService:
    """Service for handling insurance verification operations"""
    
    def __init__(self, db: AsyncSession, redis: Optional[RedisClient] = None):
        self.db = db
        self.redis = redis
        self.provider_service = ProviderService()
    
    async def verify_with_provider(
        self,
        request_id: uuid.UUID,
        provider: str,
        member_id: str,
        dob: str,
        last_name: str
    ) -> Dict[str, Any]:
        """
        Verify insurance with external provider
        """
        try:
            # Get provider configuration
            provider_config = await self.get_provider_config(provider)
            if not provider_config:
                raise ValueError(f"Provider {provider} not found or inactive")
            
            # Prepare verification request
            verification_request = {
                "member_id": member_id,
                "dob": dob,
                "last_name": last_name
            }
            
            # Call provider API
            provider_response = await self.provider_service.verify_insurance(
                provider_config,
                verification_request
            )
            
            # Store verification record
            await self.store_verification(
                request_id=request_id,
                provider_id=provider_config.id,
                member_key_hash=self.hash_member_key(member_id, dob, last_name),
                normalized_request=verification_request,
                provider_response=provider_response
            )
            
            return provider_response
            
        except Exception as e:
            logger.error("Provider verification failed", error=str(e))
            raise
    
    async def get_verification_by_id(self, request_id: uuid.UUID) -> Optional[Verification]:
        """
        Get verification record by request ID
        """
        try:
            result = await self.db.execute(
                select(Verification).where(Verification.request_id == request_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to fetch verification", error=str(e))
            return None
    
    async def get_provider_config(self, provider_name: str) -> Optional[Provider]:
        """
        Get provider configuration from database
        """
        try:
            result = await self.db.execute(
                select(Provider).where(
                    Provider.name == provider_name,
                    Provider.is_active == True
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to fetch provider config", error=str(e))
            return None
    
    async def store_verification(
        self,
        request_id: uuid.UUID,
        provider_id: uuid.UUID,
        member_key_hash: str,
        normalized_request: Dict[str, Any],
        provider_response: Dict[str, Any]
    ):
        """
        Store verification record in database
        """
        try:
            verification = Verification(
                request_id=request_id,
                provider_id=provider_id,
                member_key_hash=member_key_hash,
                normalized_request=normalized_request,
                provider_response=provider_response,
                verified_at=datetime.utcnow()
            )
            
            self.db.add(verification)
            await self.db.commit()
            
            logger.info("Verification stored successfully", request_id=str(request_id))
            
        except Exception as e:
            logger.error("Failed to store verification", error=str(e))
            await self.db.rollback()
            raise
    
    def hash_member_key(self, member_id: str, dob: str, last_name: str) -> str:
        """
        Create a hash of member identification for privacy
        """
        import hashlib
        key_string = f"{member_id}:{dob}:{last_name}".lower()
        return hashlib.sha256(key_string.encode()).hexdigest()
