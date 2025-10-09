"""
Redis in-memory database configuration and connection management
"""

# Use mock Redis for development without Redis server
from .mock_redis import MockRedisModule as redis

import json
import structlog
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.config import settings

logger = structlog.get_logger()

# Redis connection pool
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None

async def get_redis() -> redis.Redis:
    """Get Redis client instance"""
    global redis_client
    if redis_client is None:
        await init_redis()
    return redis_client

async def init_redis():
    """Initialize Redis connection"""
    global redis_pool, redis_client
    
    try:
        # Create connection pool
        redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            db=settings.REDIS_DB_INDEX,
            decode_responses=True,
            max_connections=20
        )
        
        # Create Redis client
        redis_client = redis.Redis(connection_pool=redis_pool)
        
        # Test connection
        await redis_client.ping()
        logger.info("Redis connection established successfully")
        
        # Initialize data structures if needed
        await _init_redis_structures()
        
    except Exception as e:
        logger.error("Failed to initialize Redis", error=str(e))
        raise

async def _init_redis_structures():
    """Initialize Redis data structures and indexes"""
    try:
        # Create indexes for better performance (if using RedisSearch module)
        # For now, we'll use simple key patterns
        
        # Set up any initial data or configurations
        await redis_client.set("system:initialized", "true", ex=86400)  # 24 hours
        
        logger.info("Redis data structures initialized")
    except Exception as e:
        logger.warning("Could not initialize Redis structures", error=str(e))

async def close_redis():
    """Close Redis connections"""
    global redis_client, redis_pool
    
    if redis_client:
        await redis_client.close()
        redis_client = None
    
    if redis_pool:
        await redis_pool.disconnect()
        redis_pool = None
    
    logger.info("Redis connections closed")

# Helper functions for Redis operations
class RedisHelper:
    """Helper class for Redis operations"""
    
    @staticmethod
    async def set_hash(key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set hash data with optional TTL"""
        client = await get_redis()
        
        # Convert datetime objects to ISO strings
        serialized_data = {}
        for k, v in data.items():
            if isinstance(v, datetime):
                serialized_data[k] = v.isoformat()
            elif hasattr(v, 'isoformat'):  # date objects
                serialized_data[k] = v.isoformat()
            elif isinstance(v, dict) or isinstance(v, list):
                serialized_data[k] = json.dumps(v)
            else:
                serialized_data[k] = str(v)
        
        await client.hset(key, mapping=serialized_data)
        
        if ttl:
            await client.expire(key, ttl)
        
        return True
    
    @staticmethod
    async def get_hash(key: str) -> Optional[Dict[str, str]]:
        """Get hash data"""
        client = await get_redis()
        return await client.hgetall(key)
    
    @staticmethod
    async def delete_key(key: str) -> bool:
        """Delete a key"""
        client = await get_redis()
        result = await client.delete(key)
        return result > 0
    
    @staticmethod
    async def add_to_stream(stream_key: str, data: Dict[str, Any]) -> str:
        """Add entry to Redis Stream"""
        client = await get_redis()
        
        # Serialize data
        serialized_data = {}
        for k, v in data.items():
            if isinstance(v, datetime):
                serialized_data[k] = v.isoformat()
            elif hasattr(v, 'isoformat'):  # date objects
                serialized_data[k] = v.isoformat()
            elif isinstance(v, dict) or isinstance(v, list):
                serialized_data[k] = json.dumps(v)
            else:
                serialized_data[k] = str(v)
        
        return await client.xadd(stream_key, serialized_data)
    
    @staticmethod
    async def set_with_ttl(key: str, value: str, ttl: int) -> bool:
        """Set string value with TTL"""
        client = await get_redis()
        return await client.set(key, value, ex=ttl)
    
    @staticmethod
    async def get_string(key: str) -> Optional[str]:
        """Get string value"""
        client = await get_redis()
        return await client.get(key)
