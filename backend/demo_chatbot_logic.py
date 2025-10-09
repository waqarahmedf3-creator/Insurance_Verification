#!/usr/bin/env python3
"""
Demonstration of the enhanced chatbot logic for 6-digit policy numbers
"""

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

def enhanced_chatbot_logic(message: str, session_id: str) -> dict:
    """
    Enhanced chatbot logic that handles 6-digit policy numbers
    """
    # Extract policy number from message
    policy_number = extract_policy_number(message)
    
    # Simple intent classification with enhanced policy detection
    msg_lower = message.lower()
    
    if any(word in msg_lower for word in ["hello", "hi", "hey"]):
        response = "Hello! I'm your insurance assistant. How can I help you today?"
        intent = "greeting"
        requires_followup = False
    elif policy_number:
        # Enhanced policy number handling
        status = get_policy_status(policy_number)
        response = f"Policy {policy_number} is {status}. To provide complete information, I'll need your Member ID, Date of birth, and Last name."
        intent = "get_policy_number"
        requires_followup = True
    elif any(word in msg_lower for word in ["policy", "number"]):
        response = "I can help you find your policy number. Please provide your member ID, date of birth, and last name."
        intent = "get_policy_number"
        requires_followup = True
    elif any(word in msg_lower for word in ["coverage", "covered", "active"]):
        response = "I can check your coverage status. Please provide your member ID, date of birth, and last name."
        intent = "check_coverage"
        requires_followup = True
    elif any(word in msg_lower for word in ["expire", "expiry", "expires"]):
        response = "I can check your policy expiry date. Please provide your member ID, date of birth, and last name."
        intent = "check_expiry"
        requires_followup = True
    else:
        response = "I'm here to help with insurance information. You can ask me about your policy number, coverage status, or expiry date."
        intent = "fallback"
        requires_followup = False
    
    return {
        "response": response,
        "intent": intent,
        "session_id": session_id,
        "requires_followup": requires_followup,
        "extracted_policy_number": policy_number,
        "policy_status": get_policy_status(policy_number) if policy_number else None
    }

def demonstrate_enhanced_chatbot():
    """Demonstrate the enhanced chatbot functionality"""
    
    print("🤖 Enhanced Insurance Chatbot Demo")
    print("=" * 50)
    print("This demo shows the enhanced chatbot logic that can:")
    print("✅ Extract 6+ digit policy numbers from user input")
    print("✅ Simulate different policy statuses based on the policy number")
    print("✅ Provide appropriate responses based on policy status")
    print("=" * 50)
    
    # Test cases with different policy numbers
    test_cases = [
        ("123456", "6-digit policy number (should be EXPIRED)"),
        ("123457", "6-digit policy number (should be EXPIRED)"),
        ("123458", "6-digit policy number (should be EXPIRED)"),
        ("123459", "6-digit policy number (should be PENDING)"),
        ("123450", "6-digit policy number (should be ACTIVE)"),
        ("123451", "6-digit policy number (should be ACTIVE)"),
        ("123453", "6-digit policy number (should be INACTIVE)"),
        ("Hello", "Greeting message"),
        ("I need help with my policy", "Policy request without number"),
        ("My policy number is 987654", "Policy number in sentence"),
        ("Check coverage for policy 555555", "Policy number with context"),
    ]
    
    for message, description in test_cases:
        print(f"\n📝 Input: '{message}' ({description})")
        result = enhanced_chatbot_logic(message, "demo_session")
        
        print(f"🎯 Intent: {result['intent']}")
        if result['extracted_policy_number']:
            print(f"🔍 Extracted Policy: {result['extracted_policy_number']}")
            print(f"📊 Policy Status: {result['policy_status']}")
        print(f"💬 Response: {result['response']}")
        print(f"🔄 Requires Followup: {result['requires_followup']}")
        print("-" * 40)
    
    print("\n✅ Demo completed! The enhanced chatbot can now:")
    print("• Detect 6+ digit policy numbers in user messages")
    print("• Simulate realistic policy statuses (ACTIVE, INACTIVE, EXPIRED, PENDING)")
    print("• Provide context-aware responses based on the policy status")
    print("• Handle various input formats (just numbers, sentences with numbers, etc.)")

if __name__ == "__main__":
    demonstrate_enhanced_chatbot()