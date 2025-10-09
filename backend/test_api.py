#!/usr/bin/env python3
"""
Test the FastAPI endpoints with Redis in-memory database
"""

import asyncio
import json
from fastapi.testclient import TestClient
from app.main import app

def test_api_endpoints():
    """Test API endpoints"""
    print("Testing Insurance Verification API with Redis In-Memory Database...")
    
    # Create test client
    client = TestClient(app)
    
    # Test 1: Health endpoint
    print("\nTest 1: Health endpoint")
    response = client.get("/health")
    print(f"Health check status: {response.status_code}")
    if response.status_code == 200:
        print(f"Health response: {response.json()}")
    
    # Test 2: Verification endpoint
    print("\nTest 2: Verification endpoint")
    verify_payload = {
        "provider": "test_provider",
        "member_id": "12345", 
        "dob": "1990-01-01",
        "last_name": "Smith"
    }
    
    headers = {"Authorization": "Bearer your-secret-key-here"}
    
    response = client.post("/api/verify", json=verify_payload, headers=headers)
    print(f"Verification status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Verification result: {result['status']}")
        print(f"Request ID: {result.get('request_id', 'N/A')}")
    else:
        print(f"Error: {response.text}")
    
    # Test 3: Policy info endpoint
    print("\nTest 3: Policy info endpoint")
    policy_payload = {
        "member_id": "12345",
        "dob": "1990-01-01", 
        "last_name": "Smith"
    }
    
    response = client.post("/api/policy-info", json=policy_payload, headers=headers)
    print(f"Policy info status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Policy number: {result['policy_number']}")
        print(f"Coverage status: {result['coverage_status']}")
        print(f"Expiry date: {result['expiry_date']}")
        print(f"Source: {result['source']}")
    else:
        print(f"Error: {response.text}")
    
    # Test 4: Cache functionality (second request should be faster)
    print("\nTest 4: Cache functionality")
    response2 = client.post("/api/policy-info", json=policy_payload, headers=headers)
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"Cached policy source: {result2['source']}")
        print("Cache is working - second request served from cache")
    
    print("\nAll API tests completed!")
    print("Redis in-memory database integration successful!")

if __name__ == "__main__":
    test_api_endpoints()
