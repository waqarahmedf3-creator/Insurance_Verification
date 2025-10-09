"""
Policy management API routes for CRUD operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import structlog
from uuid import UUID

from app.core.database import get_db
from app.core.redis_client import get_redis, RedisClient
from app.schemas.policy import (
    PolicyCreateRequest, 
    PolicyUpdateRequest, 
    PolicyResponse, 
    PolicyListResponse
)
from app.services.policy_service import PolicyService
from app.core.security import get_current_user

logger = structlog.get_logger()
router = APIRouter()

@router.post("/policies", response_model=PolicyResponse)
async def create_policy(
    request: PolicyCreateRequest,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    """Create a new policy"""
    try:
        policy_service = PolicyService(db, redis)
        policy_data = request.dict()
        policy = await policy_service.create_policy(policy_data)
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create policy"
            )
        
        return PolicyResponse.from_orm(policy)
        
    except Exception as e:
        logger.error("Failed to create policy", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create policy"
        )

@router.get("/policies", response_model=PolicyListResponse)
async def get_policies(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    """Get all policies with pagination and optional search"""
    try:
        policy_service = PolicyService(db, redis)
        offset = (page - 1) * page_size
        
        if search:
            policies = await policy_service.search_policies(search)
            total = len(policies)
            policies = policies[offset:offset + page_size]
        else:
            policies = await policy_service.get_all_policies(limit=page_size, offset=offset)
            total = len(policies) + offset
        
        policy_responses = [PolicyResponse.from_orm(policy) for policy in policies]
        
        return PolicyListResponse(
            policies=policy_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error("Failed to get policies", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve policies"
        )

@router.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific policy by ID"""
    try:
        policy_service = PolicyService(db, redis)
        policy = await policy_service.get_policy_by_id(str(policy_id))
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy {policy_id} not found"
            )
        
        return PolicyResponse.from_orm(policy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get policy", error=str(e), policy_id=str(policy_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve policy"
        )

@router.put("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: UUID,
    request: PolicyUpdateRequest,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    """Update a specific policy"""
    try:
        policy_service = PolicyService(db, redis)
        
        existing_policy = await policy_service.get_policy_by_id(str(policy_id))
        if not existing_policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy {policy_id} not found"
            )
        
        update_data = request.dict(exclude_unset=True)
        updated_policy = await policy_service.update_policy(str(policy_id), update_data)
        
        if not updated_policy:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update policy"
            )
        
        return PolicyResponse.from_orm(updated_policy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update policy", error=str(e), policy_id=str(policy_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update policy"
        )

@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific policy"""
    try:
        policy_service = PolicyService(db, redis)
        
        existing_policy = await policy_service.get_policy_by_id(str(policy_id))
        if not existing_policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy {policy_id} not found"
            )
        
        success = await policy_service.delete_policy(str(policy_id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete policy"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete policy", error=str(e), policy_id=str(policy_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete policy"
        )