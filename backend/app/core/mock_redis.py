"""
Mock Redis implementation for testing without Redis server
"""

import json
import time
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta


class MockRedis:
    """Mock Redis client for testing purposes"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.expiry: Dict[str, float] = {}
    
    async def ping(self) -> bool:
        """Mock ping response"""
        return True
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiry"""
        self.data[key] = value
        if ex:
            self.expiry[key] = time.time() + ex
        return True
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value by key"""
        if key in self.expiry and time.time() > self.expiry[key]:
            # Key has expired
            del self.data[key]
            del self.expiry[key]
            return None
        return self.data.get(key)
    
    async def hset(self, key: str, mapping: Dict[str, Any]) -> int:
        """Set hash fields"""
        if key not in self.data:
            self.data[key] = {}
        self.data[key].update(mapping)
        return len(mapping)
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields"""
        if key in self.expiry and time.time() > self.expiry[key]:
            # Key has expired
            del self.data[key]
            del self.expiry[key]
            return {}
        return self.data.get(key, {})
    
    async def delete(self, key: str) -> int:
        """Delete a key"""
        if key in self.data:
            del self.data[key]
            if key in self.expiry:
                del self.expiry[key]
            return 1
        return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiry for a key"""
        if key in self.data:
            self.expiry[key] = time.time() + seconds
            return True
        return False
    
    async def xadd(self, stream_key: str, data: Dict[str, Any]) -> str:
        """Add entry to stream (mock implementation)"""
        if stream_key not in self.data:
            self.data[stream_key] = []
        
        entry_id = f"{int(time.time() * 1000)}-0"
        entry = {"id": entry_id, "data": data}
        self.data[stream_key].append(entry)
        return entry_id
    
    async def close(self):
        """Close connection (no-op for mock)"""
        pass


# Global mock Redis instance
_mock_redis = MockRedis()


class MockConnectionPool:
    """Mock Redis connection pool"""
    
    @classmethod
    def from_url(cls, url: str, **kwargs):
        return cls()
    
    async def disconnect(self):
        """Mock disconnect method"""
        pass


class MockRedisModule:
    """Mock Redis module"""
    
    ConnectionPool = MockConnectionPool
    
    class Redis:
        def __init__(self, connection_pool=None):
            pass
        
        async def ping(self):
            return await _mock_redis.ping()
        
        async def set(self, key: str, value: str, ex: Optional[int] = None):
            return await _mock_redis.set(key, value, ex)
        
        async def get(self, key: str):
            return await _mock_redis.get(key)
        
        async def hset(self, key: str, mapping: Dict[str, Any]):
            return await _mock_redis.hset(key, mapping)
        
        async def hgetall(self, key: str):
            return await _mock_redis.hgetall(key)
        
        async def delete(self, key: str):
            return await _mock_redis.delete(key)
        
        async def expire(self, key: str, seconds: int):
            return await _mock_redis.expire(key, seconds)
        
        async def xadd(self, stream_key: str, data: Dict[str, Any]):
            return await _mock_redis.xadd(stream_key, data)
        
        async def close(self):
            await _mock_redis.close()
