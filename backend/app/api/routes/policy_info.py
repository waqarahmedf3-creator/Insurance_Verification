"""
Policy information API routes for chatbot queries
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from datetime import datetime

from app.core.database import get_db
from app.core.redis_client import get_redis, RedisClient
from app.schemas.verification import PolicyInfoRequest, PolicyInfoResponse
from app.services.policy_service import PolicyService
from app.core.security import get_current_user

logger = structlog.get_logger()
router = APIRouter()

@router.post("/policy-info", response_model=PolicyInfoResponse)
async def get_policy_info(
    request: PolicyInfoRequest,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    """
    Get policy information for chatbot queries
    Returns policy number, coverage status, and expiry date
    """
    try:
        policy_service = PolicyService(db, redis)
        
        # Get policy information
        policy_info = await policy_service.get_policy_info(
            member_id=request.member_id,
            dob=request.dob,
            last_name=request.last_name
        )
        
        if not policy_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy information not found"
            )
        
        return PolicyInfoResponse(
            policy_number=policy_info.get("policy_number"),
            coverage_status=policy_info.get("coverage_status"),
            expiry_date=policy_info.get("expiry_date"),
            source=policy_info.get("source", "provider"),
            verified_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get policy info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve policy information"
        )

@router.get("/policy-info/by-number", response_model=PolicyInfoResponse)
async def get_policy_info_by_number(
    policy_number: str = Query(..., description="Policy number to look up", min_length=6, max_length=20),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    """
    Get policy information by policy number for chatbot queries
    Returns policy details when given a policy number
    """
    try:
        policy_service = PolicyService(db, redis)
        
        # Get policy information by policy number
        policy_info = await policy_service.get_policy_by_number(policy_number)
        
        if not policy_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy {policy_number} not found"
            )
        
        return PolicyInfoResponse(
            policy_number=policy_info.get("policy_number"),
            coverage_status=policy_info.get("coverage_status"),
            expiry_date=policy_info.get("expiry_date"),
            source=policy_info.get("source", "provider"),
            verified_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get policy by number", error=str(e), policy_number=policy_number)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve policy information"
        )
