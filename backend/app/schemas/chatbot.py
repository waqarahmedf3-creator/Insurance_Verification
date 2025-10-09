"""
Pydantic schemas for chatbot interactions
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum

class ChatIntent(str, Enum):
    """Chatbot intent enumeration"""
    GREETING = "greeting"
    GET_POLICY_NUMBER = "get_policy_number"
    CHECK_COVERAGE = "check_coverage"
    CHECK_EXPIRY = "check_expiry"
    FALLBACK = "fallback"

class ChatMessage(BaseModel):
    """Schema for chat messages"""
    message: str = Field(..., description="User message", min_length=1)
    session_id: Optional[str] = Field(None, description="Chat session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")

class ChatResponse(BaseModel):
    """Schema for chatbot responses"""
    response: str = Field(..., description="Bot response message")
    intent: ChatIntent = Field(..., description="Detected intent")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    session_id: str = Field(..., description="Chat session identifier")
    requires_followup: bool = Field(default=False, description="Whether followup is needed")
    followup_question: Optional[str] = Field(None, description="Followup question if needed")

class ChatSession(BaseModel):
    """Schema for chat session data"""
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    context: Dict[str, Any] = Field(default_factory=dict, description="Session context")
    created_at: str = Field(..., description="Session creation timestamp")
    last_activity: str = Field(..., description="Last activity timestamp")

class IntentClassification(BaseModel):
    """Schema for intent classification results"""
    intent: ChatIntent = Field(..., description="Classified intent")
    confidence: float = Field(..., description="Classification confidence score")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")

class ChatHistory(BaseModel):
    """Schema for chat history"""
    session_id: str = Field(..., description="Session identifier")
    messages: List[Dict[str, Any]] = Field(..., description="Chat message history")
    created_at: str = Field(..., description="Session start time")
    updated_at: str = Field(..., description="Last message time")
