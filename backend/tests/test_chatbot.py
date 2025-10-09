"""
Tests for chatbot endpoints
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
def mock_chatbot_service():
    """Mock chatbot service"""
    with patch('app.services.chatbot_service.ChatbotService') as mock:
        service_instance = AsyncMock()
        service_instance.process_message.return_value = {
            "response": "Hello! How can I help you with your insurance?",
            "intent": "greeting",
            "entities": {},
            "session_id": "test-session-id",
            "requires_followup": False
        }
        mock.return_value = service_instance
        yield service_instance

def test_chat_with_bot_success(mock_auth, mock_chatbot_service):
    """Test successful chat interaction"""
    chat_data = {
        "message": "Hello",
        "session_id": "test-session-id"
    }
    
    response = client.post("/api/chat", json=chat_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "intent" in data
    assert "session_id" in data

def test_chat_with_bot_invalid_data(mock_auth):
    """Test chat with invalid data"""
    invalid_data = {
        "message": "",  # Empty message
        "session_id": "test-session-id"
    }
    
    response = client.post("/api/chat", json=invalid_data)
    
    assert response.status_code == 422  # Validation error

def test_chat_with_bot_unauthorized():
    """Test chat without authentication"""
    chat_data = {
        "message": "Hello",
        "session_id": "test-session-id"
    }
    
    response = client.post("/api/chat", json=chat_data)
    
    assert response.status_code == 401

def test_create_chat_session(mock_auth):
    """Test creating a new chat session"""
    response = client.post("/api/chat/session")
    
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "user_id" in data
    assert "created_at" in data
