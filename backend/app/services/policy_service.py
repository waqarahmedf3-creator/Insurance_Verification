"""
Policy service for handling policy information queries and CRUD operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime

from app.models.policies import Policy
from app.core.redis_client import RedisClient
from app.services.cache_service import CacheService

logger = structlog.get_logger()

class PolicyService:
    """Service for handling policy information operations"""
    
    def __init__(self, db: AsyncSession, redis: Optional[RedisClient] = None):
        self.db = db
        self.redis = redis
        self.cache_service = CacheService(redis) if redis else None
    
    async def get_policy_info(
        self,
        member_id: str,
        dob: str,
        last_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get policy information for a member
        """
        try:
            # Check cache first
            if self.cache_service:
                cache_key = self.cache_service.generate_policy_key(member_id, dob, last_name)
                cached_policy = await self.cache_service.get_policy(cache_key)
                if cached_policy:
                    logger.info("Policy cache hit", member_id=member_id)
                    return cached_policy
            
            # Query database
            member_key_hash = self.hash_member_key(member_id, dob, last_name)
            policy = await self.get_policy_by_member_hash(member_key_hash)
            
            if not policy:
                logger.info("Policy not found", member_id=member_id)
                return None
            
            policy_info = {
                "policy_number": policy.policy_number,
                "coverage_status": policy.coverage_status.value,
                "expiry_date": policy.expiry_date,
                "source": policy.source.value,
                "verified_at": policy.verified_at
            }
            
            # Cache the result
            if self.cache_service:
                await self.cache_service.cache_policy(cache_key, policy_info)
            
            return policy_info
            
        except Exception as e:
            logger.error("Failed to get policy info", error=str(e))
            return None
    
    async def get_policy_by_member_hash(self, member_key_hash: str) -> Optional[Policy]:
        """
        Get policy by member key hash
        """
        try:
            result = await self.db.execute(
                select(Policy).where(Policy.member_id == member_key_hash)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to fetch policy", error=str(e))
            return None
    
    async def cache_policy_info(
        self,
        member_id: str,
        dob: str,
        last_name: str,
        policy_data: Dict[str, Any]
    ):
        """
        Cache policy information
        """
        try:
            if not self.cache_service:
                return
            
            cache_key = self.cache_service.generate_policy_key(member_id, dob, last_name)
            await self.cache_service.cache_policy(cache_key, policy_data)
            
            logger.info("Policy info cached", member_id=member_id)
            
        except Exception as e:
            logger.error("Failed to cache policy info", error=str(e))
    
    def hash_member_key(self, member_id: str, dob: str, last_name: str) -> str:
        """
        Create a hash of member identification for privacy
        """
        import hashlib
        key_string = f"{member_id}:{dob}:{last_name}".lower()
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    async def get_policy_by_number(self, policy_number: str) -> Optional[Dict[str, Any]]:
        """
        Get policy information by policy number
        """
        try:
            # Check cache first
            if self.cache_service:
                cache_key = f"policy_number:{policy_number}"
                cached_policy = await self.cache_service.get_policy(cache_key)
                if cached_policy:
                    logger.info("Policy cache hit by number", policy_number=policy_number)
                    return cached_policy
            
            # Query database
            policy = await self.get_policy_by_number_from_db(policy_number)
            
            if not policy:
                logger.info("Policy not found by number", policy_number=policy_number)
                return None
            
            policy_info = {
                "policy_number": policy.policy_number,
                "coverage_status": policy.coverage_status.value,
                "expiry_date": policy.expiry_date,
                "source": policy.source.value,
                "verified_at": policy.verified_at
            }
            
            # Cache the result
            if self.cache_service:
                await self.cache_service.cache_policy(cache_key, policy_info)
            
            return policy_info
            
        except Exception as e:
            logger.error("Failed to get policy by number", error=str(e), policy_number=policy_number)
            return None
    
    async def get_policy_by_number_from_db(self, policy_number: str) -> Optional[Policy]:
        """
        Get policy by policy number from database
        """
        try:
            result = await self.db.execute(
                select(Policy).where(Policy.policy_number == policy_number)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to fetch policy by number", error=str(e), policy_number=policy_number)
            return None
    
    # CRUD Operations for Policy Management
    
    async def create_policy(self, policy_data: Dict[str, Any]) -> Optional[Policy]:
        """
        Create a new policy
        """
        try:
            # Convert date strings to datetime objects
            if policy_data.get('dob'):
                policy_data['dob'] = datetime.strptime(policy_data['dob'], '%Y-%m-%d')
            if policy_data.get('expiry_date'):
                policy_data['expiry_date'] = datetime.strptime(policy_data['expiry_date'], '%Y-%m-%d')
            
            policy = Policy(**policy_data)
            self.db.add(policy)
            await self.db.commit()
            await self.db.refresh(policy)
            
            logger.info("Policy created successfully", policy_id=str(policy.id))
            return policy
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to create policy", error=str(e))
            return None
    
    async def get_policy_by_id(self, policy_id: str) -> Optional[Policy]:
        """
        Get policy by ID
        """
        try:
            result = await self.db.execute(
                select(Policy).where(Policy.id == policy_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to fetch policy by ID", error=str(e), policy_id=policy_id)
            return None
    
    async def get_all_policies(self, limit: int = 100, offset: int = 0) -> List[Policy]:
        """
        Get all policies with pagination
        """
        try:
            result = await self.db.execute(
                select(Policy).order_by(Policy.created_at.desc()).limit(limit).offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error("Failed to fetch policies", error=str(e))
            return []
    
    async def update_policy(self, policy_id: str, update_data: Dict[str, Any]) -> Optional[Policy]:
        """
        Update a policy
        """
        try:
            # Convert date strings to datetime objects if provided
            if update_data.get('dob'):
                update_data['dob'] = datetime.strptime(update_data['dob'], '%Y-%m-%d')
            if update_data.get('expiry_date'):
                update_data['expiry_date'] = datetime.strptime(update_data['expiry_date'], '%Y-%m-%d')
            
            # Update the policy
            await self.db.execute(
                update(Policy).where(Policy.id == policy_id).values(**update_data)
            )
            await self.db.commit()
            
            # Fetch the updated policy
            policy = await self.get_policy_by_id(policy_id)
            logger.info("Policy updated successfully", policy_id=policy_id)
            return policy
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to update policy", error=str(e), policy_id=policy_id)
            return None
    
    async def delete_policy(self, policy_id: str) -> bool:
        """
        Delete a policy
        """
        try:
            result = await self.db.execute(
                delete(Policy).where(Policy.id == policy_id)
            )
            await self.db.commit()
            
            if result.rowcount > 0:
                logger.info("Policy deleted successfully", policy_id=policy_id)
                return True
            else:
                logger.warning("Policy not found for deletion", policy_id=policy_id)
                return False
                
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to delete policy", error=str(e), policy_id=policy_id)
            return False
    
    async def search_policies(self, search_term: str) -> List[Policy]:
        """
        Search policies by various fields
        """
        try:
            # Search in provider, member_id, policy_number, first_name, last_name, email
            result = await self.db.execute(
                select(Policy).where(
                    (Policy.provider.ilike(f"%{search_term}%")) |
                    (Policy.member_id.ilike(f"%{search_term}%")) |
                    (Policy.policy_number.ilike(f"%{search_term}%")) |
                    (Policy.first_name.ilike(f"%{search_term}%")) |
                    (Policy.last_name.ilike(f"%{search_term}%")) |
                    (Policy.email.ilike(f"%{search_term}%"))
                ).order_by(Policy.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error("Failed to search policies", error=str(e))
            return []
