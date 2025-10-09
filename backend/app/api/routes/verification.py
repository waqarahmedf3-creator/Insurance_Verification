"""
Verification API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import uuid
import structlog
from datetime import datetime

from app.core.database import get_db
from app.core.redis_client import get_redis, RedisClient
from app.schemas.verification import (
    VerificationRequest, 
    VerificationResponse, 
    VerificationDetailsResponse,
    PolicyInfoRequest,
    PolicyInfoResponse
)
from app.services.verification_service import VerificationService
from app.services.cache_service import CacheService
from app.core.security import get_current_user

logger = structlog.get_logger()
router = APIRouter()

@router.post("/verify", response_model=VerificationResponse)
async def verify_insurance(
    request: VerificationRequest,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    """
    Verify insurance details via external provider APIs
    """
    try:
        request_id = uuid.uuid4()
        
        # Initialize services
        verification_service = VerificationService(db, redis)
        cache_service = CacheService(redis)
        
        # Check cache first
        cache_key = cache_service.generate_verification_key(
            request.provider, 
            request.member_id, 
            request.dob, 
            request.last_name
        )
        
        cached_result = await cache_service.get_verification(cache_key)
        if cached_result:
            logger.info("Cache hit for verification", request_id=str(request_id))
            return VerificationResponse(
                request_id=request_id,
                status="verified",
                verified_at=datetime.utcnow(),
                source="cache",
                provider_response=cached_result
            )
        
        # Verify with provider
        logger.info("Cache miss, verifying with provider", request_id=str(request_id))
        verification_result = await verification_service.verify_with_provider(
            request_id=request_id,
            provider=request.provider,
            member_id=request.member_id,
            dob=request.dob,
            last_name=request.last_name
        )
        
        # Cache the result
        await cache_service.cache_verification(cache_key, verification_result)
        
        return VerificationResponse(
            request_id=request_id,
            status="verified",
            verified_at=datetime.utcnow(),
            source="provider",
            provider_response=verification_result
        )
        
    except Exception as e:
        logger.error("Verification failed", error=str(e), request_id=str(request_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )

@router.get("/verify/{request_id}", response_model=VerificationDetailsResponse)
async def get_verification_details(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch stored verification details by request ID
    """
    try:
        verification_service = VerificationService(db, None)
        verification = await verification_service.get_verification_by_id(request_id)
        
        if not verification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification not found"
            )
        
        return VerificationDetailsResponse.from_orm(verification)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch verification details", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch verification details"
        )
