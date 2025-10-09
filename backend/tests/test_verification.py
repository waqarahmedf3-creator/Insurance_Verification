"""
Tests for verification endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from main import app

client = TestClient(app)

@pytest.fixture
def mock_auth():
    """Mock authentication"""
    with patch('app.core.security.get_current_user') as mock:
        mock.return_value = {
            "id": "test-user-id",
            "email": "test@example.com",
            "full_name": "Test User"
        }
        yield mock

@pytest.fixture
def mock_verification_service():
    """Mock verification service"""
    with patch('app.services.verification_service.VerificationService') as mock:
        service_instance = AsyncMock()
        service_instance.verify_with_provider.return_value = {
            "status": "verified",
            "policy_number": "POL123456789",
            "coverage_status": "active"
        }
        mock.return_value = service_instance
        yield service_instance

def test_verify_insurance_success(mock_auth, mock_verification_service):
    """Test successful insurance verification"""
    verification_data = {
        "provider": "provider_a",
        "member_id": "MEMBER123",
        "dob": "1990-01-01",
        "last_name": "Smith"
    }
    
    response = client.post("/api/verify", json=verification_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["status"] == "verified"
    assert data["source"] in ["cache", "provider"]

def test_verify_insurance_invalid_data(mock_auth):
    """Test verification with invalid data"""
    invalid_data = {
        "provider": "provider_a",
        "member_id": "",  # Empty member ID
        "dob": "invalid-date",
        "last_name": "Smith"
    }
    
    response = client.post("/api/verify", json=invalid_data)
    
    assert response.status_code == 422  # Validation error

def test_verify_insurance_unauthorized():
    """Test verification without authentication"""
    verification_data = {
        "provider": "provider_a",
        "member_id": "MEMBER123",
        "dob": "1990-01-01",
        "last_name": "Smith"
    }
    
    response = client.post("/api/verify", json=verification_data)
    
    assert response.status_code == 401

def test_get_verification_details(mock_auth, mock_verification_service):
    """Test getting verification details"""
    request_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # Mock the get_verification_by_id method
    mock_verification = AsyncMock()
    mock_verification.id = request_id
    mock_verification.request_id = request_id
    mock_verification.provider_name = "provider_a"
    mock_verification.member_key_hash = "hashed_key"
    mock_verification.normalized_request = {"member_id": "MEMBER123"}
    mock_verification.provider_response = {"status": "verified"}
    mock_verification.source = "provider"
    mock_verification.verified_at = "2024-01-01T00:00:00Z"
    mock_verification.created_at = "2024-01-01T00:00:00Z"
    
    mock_verification_service.get_verification_by_id.return_value = mock_verification
    
    response = client.get(f"/api/verify/{request_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == request_id
