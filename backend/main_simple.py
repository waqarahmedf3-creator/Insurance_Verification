"""
Simplified Insurance Verification System - FastAPI Backend
This is a minimal version for demonstration without complex dependencies
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
import json

app = FastAPI(
    title="Insurance Verification System",
    description="Simplified insurance verification with AI chatbot assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage for demo
verifications = {}
users = {}
chat_sessions = {}

# Pydantic models
class VerificationRequest(BaseModel):
    provider: str
    member_id: str
    dob: str
    last_name: str

class VerificationResponse(BaseModel):
    request_id: str
    status: str
    verified_at: str
    source: str
    provider_response: Dict[str, Any]

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    session_id: str
    requires_followup: bool = False

# Mock authentication (simplified)
def get_current_user():
    return {"id": "demo-user", "email": "demo@example.com", "full_name": "Demo User"}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Insurance Verification System API", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": "development"
    }

# Authentication endpoints
@app.post("/api/auth/register")
async def register_user(user_data: UserCreate):
    """Register a new user (simplified)"""
    user_id = str(uuid.uuid4())
    users[user_id] = {
        "id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "created_at": datetime.utcnow().isoformat()
    }
    return users[user_id]

@app.post("/api/auth/login")
async def login_user(login_data: UserLogin):
    """Login user (simplified)"""
    # Simple mock login - in real app, verify password
    return {
        "access_token": "demo-token-123",
        "token_type": "bearer",
        "expires_in": 1800
    }

@app.get("/api/auth/me")
async def get_current_user_info():
    """Get current user information"""
    return get_current_user()

# Verification endpoints
@app.post("/api/verify", response_model=VerificationResponse)
async def verify_insurance(request: VerificationRequest):
    """
    Verify insurance details (enhanced mock implementation)
    """
    request_id = str(uuid.uuid4())
    
    # Determine scenario based on last digit of member ID
    last_digit = int(request.member_id[-1]) if request.member_id and request.member_id[-1].isdigit() else 0
    
    if last_digit in [0, 1, 2]:
        status = "active"
        expiry_date = "2025-12-31"
        premium_status = "paid"
        coverage_amount = "$50,000"
        message = "Policy is active and in good standing"
    elif last_digit in [3, 4]:
        status = "expired"
        expiry_date = "2024-06-15"
        premium_status = "overdue"
        coverage_amount = "$0"
        message = "Policy has expired. Please contact your agent to renew"
    elif last_digit in [5, 6]:
        status = "suspended"
        expiry_date = "2025-03-31"
        premium_status = "overdue"
        coverage_amount = "$0"
        message = "Policy is suspended due to non-payment of premiums"
    elif last_digit == 7:
        # Policy not found scenario
        return VerificationResponse(
            request_id=request_id,
            status="not_found",
            verified_at=datetime.utcnow().isoformat(),
            source="provider",
            provider_response={
                "policy_number": f"POL{request.member_id[:6].upper()}",
                "member_id": request.member_id,
                "member_name": f"{request.last_name.title()}, John",
                "provider": request.provider.title(),
                "coverage_status": "not_found",
                "expiry_date": None,
                "premium_status": None,
                "coverage_amount": None,
                "plan_type": "Health Insurance Premium",
                "last_payment_date": None,
                "message": f"No policy found for member ID {request.member_id} with {request.provider}"
            }
        )
    elif last_digit == 8:
        status = "pending_verification"
        expiry_date = "2025-12-31"
        premium_status = "under_review"
        coverage_amount = "TBD"
        message = "Policy verification is pending. Please allow 24-48 hours for processing"
    else:
        status = "grace_period"
        expiry_date = "2025-01-15"
        premium_status = "grace_period"
        coverage_amount = "$50,000"
        message = "Policy is in grace period. Payment required within 30 days"

    policy_number = f"POL{request.provider[:3].upper()}{request.member_id[:6]}"
    
    mock_response = {
        "policy_number": policy_number,
        "member_id": request.member_id,
        "member_name": f"{request.last_name.title()}, John",
        "provider": request.provider.title(),
        "coverage_status": status,
        "expiry_date": expiry_date,
        "premium_status": premium_status,
        "coverage_amount": coverage_amount,
        "plan_type": "Health Insurance Premium",
        "last_payment_date": "2024-01-15" if status != "not_found" else None,
        "message": message
    }
    
    # Store verification
    verifications[request_id] = {
        "request_id": request_id,
        "provider": request.provider,
        "member_id": request.member_id,
        "verified_at": datetime.utcnow().isoformat(),
        "response": mock_response
    }
    
    return VerificationResponse(
        request_id=request_id,
        status="verified" if status in ["active", "expired", "suspended", "grace_period", "pending_verification"] else "not_found",
        verified_at=datetime.utcnow().isoformat(),
        source="provider",
        provider_response=mock_response
    )

@app.get("/api/verify/{request_id}")
async def get_verification_details(request_id: str):
    """Get verification details"""
    if request_id not in verifications:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    return verifications[request_id]

@app.post("/api/policy-info")
async def get_policy_info(request: VerificationRequest):
    """Get policy information for chatbot"""
    # Determine scenario based on last digit of member ID
    last_digit = int(request.member_id[-1]) if request.member_id and request.member_id[-1].isdigit() else 0
    
    if last_digit in [0, 1, 2]:
        status = "active"
        expiry_date = "2025-12-31"
        premium_status = "paid"
        coverage_amount = "$50,000"
    elif last_digit in [3, 4]:
        status = "expired"
        expiry_date = "2024-06-15"
        premium_status = "overdue"
        coverage_amount = "$0"
    elif last_digit in [5, 6]:
        status = "suspended"
        expiry_date = "2025-03-31"
        premium_status = "overdue"
        coverage_amount = "$0"
    elif last_digit == 7:
        return {
            "error": "Policy not found in our records",
            "error_code": "POLICY_NOT_FOUND",
            "member_id": request.member_id
        }
    elif last_digit == 8:
        status = "pending_verification"
        expiry_date = "2025-12-31"
        premium_status = "under_review"
        coverage_amount = "TBD"
    else:
        status = "grace_period"
        expiry_date = "2025-01-15"
        premium_status = "grace_period"
        coverage_amount = "$50,000"

    return {
        "policy_number": f"POL{request.member_id[:6].upper()}",
        "member_id": request.member_id,
        "coverage_status": status,
        "expiry_date": expiry_date,
        "premium_status": premium_status,
        "coverage_amount": coverage_amount,
        "plan_type": "Health Insurance Premium",
        "source": "policy_database",
        "verified_at": datetime.utcnow().isoformat(),
        "next_payment_due": "2025-02-01" if status in ["active", "grace_period"] else None
    }

@app.get("/api/policy-info/by-number")
async def get_policy_info_by_number(policyNumber: str):
    """Get policy information by policy number (for frontend integration)"""
    # Enhanced policy number handling - extract 6+ digit numbers
    policy_number = extract_policy_number(policyNumber)
    
    if not policy_number:
        return {
            "policy_number": policyNumber,
            "coverage_status": "not_found",
            "expiry_date": None,
            "source": "direct",
            "message": f"Policy number {policyNumber} was not found in our records. Could you please double-check the number again?"
        }
    
    # Get policy status based on enhanced logic
    status = get_policy_status(policy_number)
    
    # Map status to expiry dates for consistency
    status_dates = {
        "ACTIVE": "2024-12-31",
        "INACTIVE": "2023-06-15", 
        "EXPIRED": "2023-01-01",
        "PENDING": "2024-03-30"
    }
    
    # Map policy numbers to providers for more realistic data
    providers = ["State Life", "EFU", "Jubilee", "Adamjee", "IGI"]
    provider_index = int(policy_number) % len(providers)
    provider_name = providers[provider_index]
    
    return {
        "policy_number": policy_number,
        "coverage_status": status.lower(),
        "expiry_date": status_dates.get(status, "2024-12-31"),
        "source": "direct",
        "provider_name": provider_name,
        "message": f"Policy {policy_number} found with status: {status}"
    }

# Policy management endpoints (simplified)
policies_db = {}

class PolicyCreateRequest(BaseModel):
    provider: str
    member_id: str
    policy_number: str
    first_name: str
    last_name: str
    dob: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    policy_type: Optional[str] = None
    coverage_status: Optional[str] = None
    expiry_date: Optional[str] = None
    coverage_amount: Optional[float] = None
    premium_amount: Optional[float] = None

class PolicyUpdateRequest(BaseModel):
    provider: Optional[str] = None
    member_id: Optional[str] = None
    policy_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    policy_type: Optional[str] = None
    coverage_status: Optional[str] = None
    expiry_date: Optional[str] = None
    coverage_amount: Optional[float] = None
    premium_amount: Optional[float] = None

class PolicyResponse(BaseModel):
    id: str
    provider: str
    member_id: str
    policy_number: str
    first_name: str
    last_name: str
    dob: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    policy_type: Optional[str] = None
    coverage_status: Optional[str] = None
    expiry_date: Optional[str] = None
    coverage_amount: Optional[float] = None
    premium_amount: Optional[float] = None
    created_at: str
    updated_at: str

@app.post("/api/policies", response_model=PolicyResponse)
async def create_policy(request: PolicyCreateRequest):
    """Create a new policy"""
    policy_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    policy_data = {
        "id": policy_id,
        "provider": request.provider,
        "member_id": request.member_id,
        "policy_number": request.policy_number,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "dob": request.dob,
        "email": request.email,
        "phone": request.phone,
        "address": request.address,
        "zip_code": request.zip_code,
        "city": request.city,
        "state_province": request.state_province,
        "policy_type": request.policy_type,
        "coverage_status": request.coverage_status,
        "expiry_date": request.expiry_date,
        "coverage_amount": request.coverage_amount,
        "premium_amount": request.premium_amount,
        "created_at": now,
        "updated_at": now
    }
    
    policies_db[policy_id] = policy_data
    return PolicyResponse(**policy_data)

@app.get("/api/policies")
async def get_policies():
    """Get all policies"""
    return {"policies": list(policies_db.values())}

@app.get("/api/policies/by-number", response_model=PolicyResponse)
async def get_policy_by_number(policyNumber: str):
    """Get a single saved policy by policy number (case-insensitive match)"""
    for p in policies_db.values():
        if str(p.get("policy_number", "")).lower() == str(policyNumber).lower():
            return PolicyResponse(**p)
    raise HTTPException(status_code=404, detail="Policy not found")

@app.get("/api/policies/by-member")
async def get_policies_by_member(first_name: str, last_name: str):
    """Get saved policies by member first/last name (case-insensitive)"""
    fn = first_name.strip().lower()
    ln = last_name.strip().lower()
    matches = [p for p in policies_db.values() if str(p.get("first_name", "")).strip().lower() == fn and str(p.get("last_name", "")).strip().lower() == ln]
    return {"policies": matches}

@app.put("/api/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(policy_id: str, request: PolicyUpdateRequest):
    """Update a specific policy"""
    if policy_id not in policies_db:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy_data = policies_db[policy_id]
    update_data = request.dict(exclude_unset=True)
    
    # Update fields
    for key, value in update_data.items():
        if value is not None:
            policy_data[key] = value
    
    policy_data["updated_at"] = datetime.utcnow().isoformat()
    policies_db[policy_id] = policy_data
    
    return PolicyResponse(**policy_data)

@app.delete("/api/policies/{policy_id}")
async def delete_policy(policy_id: str):
    """Delete a specific policy"""
    if policy_id not in policies_db:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    del policies_db[policy_id]
    return {"message": "Policy deleted successfully"}

# Enhanced chatbot logic
import re

def extract_policy_number(message: str) -> str:
    """Extract 6+ digit policy numbers from message"""
    # Look for 6+ digit numbers
    policy_numbers = re.findall(r'\b\d{6,}\b', message)
    if policy_numbers:
        return policy_numbers[0]
    
    # Fallback: look for alphanumeric patterns
    policy_match = re.search(r'[A-Z0-9]{6,}', message)
    if policy_match:
        return policy_match.group()
    
    return None

def get_policy_status(policy_number: str) -> str:
    """Simulate different policy statuses based on policy number"""
    if not policy_number:
        return "UNKNOWN"
    
    # Extract last digit to determine status (for testing purposes)
    last_digit = int(policy_number[-1]) if policy_number[-1].isdigit() else 0
    
    if last_digit in [0, 1, 2]:
        return "ACTIVE"
    elif last_digit in [3, 4, 5]:
        return "INACTIVE"
    elif last_digit in [6, 7, 8]:
        return "EXPIRED"
    else:
        return "PENDING"

# Chatbot endpoints
@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_bot(message: ChatMessage):
    """
    Enhanced chat with AI assistant supporting 6-digit policy numbers
    """
    session_id = message.session_id or str(uuid.uuid4())
    
    # Extract policy number from message
    policy_number = extract_policy_number(message.message)
    
    # Simple intent classification with enhanced policy detection
    msg_lower = message.message.lower()
    
    if any(word in msg_lower for word in ["hello", "hi", "hey"]):
        response = "Hello! I'm your insurance assistant. How can I help you today?"
        intent = "greeting"
    elif policy_number:
        # Enhanced policy number handling
        status = get_policy_status(policy_number)
        response = f"Policy {policy_number} is {status}. To provide complete information, I'll need your Member ID, Date of birth, and Last name."
        intent = "get_policy_number"
    elif any(word in msg_lower for word in ["policy", "number"]):
        response = "I can help you find your policy number. Please provide your member ID, date of birth, and last name."
        intent = "get_policy_number"
    elif any(word in msg_lower for word in ["coverage", "covered", "active"]):
        response = "I can check your coverage status. Please provide your member ID, date of birth, and last name."
        intent = "check_coverage"
    elif any(word in msg_lower for word in ["expire", "expiry", "expires"]):
        response = "I can check your policy expiry date. Please provide your member ID, date of birth, and last name."
        intent = "check_expiry"
    else:
        response = "I'm here to help with insurance information. You can ask me about your policy number, coverage status, or expiry date."
        intent = "fallback"
    
    return ChatResponse(
        response=response,
        intent=intent,
        session_id=session_id,
        requires_followup=intent != "greeting"
    )

@app.post("/api/chat/session")
async def create_chat_session():
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = {
        "session_id": session_id,
        "user_id": "demo-user",
        "created_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat()
    }
    return chat_sessions[session_id]

@app.get("/api/chat/session/{session_id}")
async def get_chat_session(session_id: str):
    """Get chat session"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return chat_sessions[session_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_simple:app", host="0.0.0.0", port=8000, reload=True)
