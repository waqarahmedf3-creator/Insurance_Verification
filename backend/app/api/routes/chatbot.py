"""
Chatbot API routes for conversational interactions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from typing import Dict, Any

from app.core.database import get_db
from app.core.redis_client import get_redis, RedisClient
from app.schemas.chatbot import ChatMessage, ChatResponse, ChatSession
from app.services.chatbot_service import ChatbotService
from app.services.policy_service import PolicyService
from app.core.security import get_current_user

logger = structlog.get_logger()
router = APIRouter()

# Initialize chatbot service
chatbot_service = ChatbotService()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(
    message: ChatMessage,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    """
    Chat with the AI assistant
    """
    try:
        # Process the message
        response = await chatbot_service.process_message(message)
        
        # If the response requires policy information, fetch it
        if (response.intent in ["get_policy_number", "check_coverage", "check_expiry"] 
            and not response.requires_followup):
            
            # Extract member information from entities or session context
            member_info = await _extract_member_info(message, response)
            
            if member_info:
                policy_service = PolicyService(db, redis)
                policy_info = await policy_service.get_policy_info(
                    member_info["member_id"],
                    member_info["dob"],
                    member_info["last_name"]
                )
                
                if policy_info:
                    response.response = _format_policy_response(response.intent, policy_info)
                else:
                    response.response = "I couldn't find your policy information. Please verify your details and try again."
        
        # Log the chat interaction
        await _log_chat_interaction(current_user["id"], message, response)
        
        return response
        
    except Exception as e:
        logger.error("Chat processing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat processing failed"
        )

@router.get("/chat/session/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: str,
    redis: RedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    """
    Get chat session information
    """
    try:
        # Get session from Redis
        session_key = f"chat_session:{session_id}"
        session_data = await redis.get(session_key)
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return ChatSession(**session_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get chat session", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat session"
        )

@router.post("/chat/session", response_model=ChatSession)
async def create_chat_session(
    redis: RedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new chat session
    """
    try:
        import uuid
        from datetime import datetime
        
        session_id = str(uuid.uuid4())
        session = ChatSession(
            session_id=session_id,
            user_id=current_user["id"],
            context={},
            created_at=datetime.utcnow().isoformat(),
            last_activity=datetime.utcnow().isoformat()
        )
        
        # Store session in Redis
        session_key = f"chat_session:{session_id}"
        await redis.set(session_key, session.dict(), ttl=3600)  # 1 hour TTL
        
        return session
        
    except Exception as e:
        logger.error("Failed to create chat session", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )

async def _extract_member_info(message: ChatMessage, response: ChatResponse) -> Dict[str, Any]:
    """
    Extract member information from message or session context
    """
    # This is a simplified implementation
    # In production, you'd extract this from the message entities or session context
    return None

def _format_policy_response(intent: str, policy_info: Dict[str, Any]) -> str:
    """
    Format policy information for chat response
    """
    if intent == "get_policy_number":
        return f"Your policy number is: {policy_info.get('policy_number', 'Not available')}"
    
    elif intent == "check_coverage":
        status = policy_info.get('coverage_status', 'unknown')
        if status == 'active':
            return "Yes, your insurance coverage is currently active."
        elif status == 'inactive':
            return "Your insurance coverage is currently inactive."
        else:
            return f"Your coverage status is: {status}"
    
    elif intent == "check_expiry":
        expiry_date = policy_info.get('expiry_date')
        if expiry_date:
            return f"Your policy expires on: {expiry_date}"
        else:
            return "Expiry date information is not available."
    
    return "Here's your policy information."

async def _log_chat_interaction(user_id: str, message: ChatMessage, response: ChatResponse):
    """
    Log chat interaction for auditing
    """
    try:
        # This would log to the audit_logs table
        logger.info(
            "Chat interaction logged",
            user_id=user_id,
            message=message.message,
            intent=response.intent,
            session_id=response.session_id
        )
    except Exception as e:
        logger.error("Failed to log chat interaction", error=str(e))
