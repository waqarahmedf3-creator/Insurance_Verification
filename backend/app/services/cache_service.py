"""
Cache service for managing Redis cache operations
"""

from typing import Dict, Any, Optional
import structlog
from app.core.redis_client import RedisClient
from app.core.config import settings

logger = structlog.get_logger()

class CacheService:
    """Service for managing cache operations"""
    
    def __init__(self, redis: RedisClient):
        self.redis = redis
        self.default_ttl = settings.DEFAULT_CACHE_TTL
    
    def generate_verification_key(
        self,
        provider: str,
        member_id: str,
        dob: str,
        last_name: str
    ) -> str:
        """
        Generate cache key for verification requests
        """
        import hashlib
        key_string = f"verification:{provider}:{member_id}:{dob}:{last_name}".lower()
        return f"verification:{hashlib.sha256(key_string.encode()).hexdigest()}"
    
    def generate_policy_key(
        self,
        member_id: str,
        dob: str,
        last_name: str
    ) -> str:
        """
        Generate cache key for policy information
        """
        import hashlib
        key_string = f"policy:{member_id}:{dob}:{last_name}".lower()
        return f"policy:{hashlib.sha256(key_string.encode()).hexdigest()}"
    
    async def get_verification(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get verification result from cache
        """
        try:
            return await self.redis.get(cache_key)
        except Exception as e:
            logger.error("Failed to get verification from cache", error=str(e))
            return None
    
    async def cache_verification(self, cache_key: str, data: Dict[str, Any], ttl: Optional[int] = None):
        """
        Cache verification result
        """
        try:
            ttl = ttl or self.default_ttl
            await self.redis.set(cache_key, data, ttl)
            logger.info("Verification cached", key=cache_key)
        except Exception as e:
            logger.error("Failed to cache verification", error=str(e))
    
    async def get_policy(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get policy information from cache
        """
        try:
            return await self.redis.get(cache_key)
        except Exception as e:
            logger.error("Failed to get policy from cache", error=str(e))
            return None
    
    async def cache_policy(self, cache_key: str, data: Dict[str, Any], ttl: Optional[int] = None):
        """
        Cache policy information
        """
        try:
            ttl = ttl or self.default_ttl
            await self.redis.set(cache_key, data, ttl)
            logger.info("Policy cached", key=cache_key)
        except Exception as e:
            logger.error("Failed to cache policy", error=str(e))
    
    async def invalidate_verification(self, cache_key: str):
        """
        Invalidate verification cache entry
        """
        try:
            await self.redis.delete(cache_key)
            logger.info("Verification cache invalidated", key=cache_key)
        except Exception as e:
            logger.error("Failed to invalidate verification cache", error=str(e))
    
    async def invalidate_policy(self, cache_key: str):
        """
        Invalidate policy cache entry
        """
        try:
            await self.redis.delete(cache_key)
            logger.info("Policy cache invalidated", key=cache_key)
        except Exception as e:
            logger.error("Failed to invalidate policy cache", error=str(e))
    
    async def clear_all_cache(self):
        """
        Clear all cache entries (use with caution)
        """
        try:
            # This would need to be implemented based on Redis client capabilities
            logger.warning("Clear all cache requested - not implemented")
        except Exception as e:
            logger.error("Failed to clear cache", error=str(e))
