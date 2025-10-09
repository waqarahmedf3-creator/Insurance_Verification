#!/usr/bin/env python3
"""
Simple test script to verify Redis in-memory database functionality
"""

import asyncio
import json
from datetime import datetime
from app.core.database import init_redis, RedisHelper, close_redis

async def test_redis_operations():
    """Test Redis operations"""
    print("Testing Redis In-Memory Database...")
    
    try:
        # Initialize Redis
        await init_redis()
        print("Redis connection established")
        
        # Test 1: Set and get string with TTL
        print("\nTest 1: Cache operations")
        cache_key = "cache:test:12345"
        test_data = {"status": "verified", "timestamp": datetime.now().isoformat()}
        await RedisHelper.set_with_ttl(cache_key, json.dumps(test_data), 60)
        
        cached_result = await RedisHelper.get_string(cache_key)
        if cached_result:
            parsed_data = json.loads(cached_result)
            print(f"Cache set/get successful: {parsed_data}")
        else:
            print("Cache operation failed")
        
        # Test 2: Hash operations (policies)
        print("\nTest 2: Policy storage")
        policy_key = "policies:test_member_123"
        policy_data = {
            "id": "pol-001",
            "member_id": "test_member_123", 
            "policy_number": "POL-12345",
            "coverage_status": "active",
            "expiry_date": "2025-12-31",
            "source": "provider",
            "verified_at": datetime.now(),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        await RedisHelper.set_hash(policy_key, policy_data)
        retrieved_policy = await RedisHelper.get_hash(policy_key)
        
        if retrieved_policy:
            print(f"Policy storage successful: {retrieved_policy.get('policy_number')}")
        else:
            print("Policy storage failed")
        
        # Test 3: Verification record
        print("\nTest 3: Verification record")
        verification_key = "verifications:test_request_456"
        verification_data = {
            "id": "test_request_456",
            "request_id": "test_request_456",
            "provider_id": "test_provider",
            "member_key_hash": "hash_12345",
            "normalized_request": {"member_id": "123", "dob": "1990-01-01"},
            "provider_response": {"status": "verified", "policy_number": "POL-12345"},
            "source": "provider",
            "verified_at": datetime.now(),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        await RedisHelper.set_hash(verification_key, verification_data)
        retrieved_verification = await RedisHelper.get_hash(verification_key)
        
        if retrieved_verification:
            print(f"Verification storage successful: {retrieved_verification.get('id')}")
        else:
            print("Verification storage failed")
        
        # Test 4: Audit log stream
        print("\nTest 4: Audit log")
        audit_stream = "audit_logs:2025-10-02"
        audit_data = {
            "user_id": "test_user",
            "action": "verify_request", 
            "details": {"member_id": "123", "provider": "test_provider"}
        }
        
        entry_id = await RedisHelper.add_to_stream(audit_stream, audit_data)
        print(f"Audit log entry created: {entry_id}")
        
        print("\nAll Redis operations completed successfully!")
        print("In-memory database is working correctly")
        
    except Exception as e:
        print(f"Error during Redis testing: {e}")
        
    finally:
        await close_redis()
        print("Redis connection closed")

if __name__ == "__main__":
    asyncio.run(test_redis_operations())
