#!/usr/bin/env python3
"""
Direct test of the enhanced chatbot service
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.chatbot_service import ChatbotService

def test_chatbot():
    """Test the enhanced chatbot with policy numbers"""
    service = ChatbotService()
    
    # Test cases with different policy numbers
    test_cases = [
        "123456",    # Should be ACTIVE (ends in 6, but 6 is in [6,7,8] so EXPIRED)
        "123457",    # Should be EXPIRED (ends in 7)
        "123458",    # Should be EXPIRED (ends in 8)
        "123459",    # Should be PENDING (ends in 9)
        "123450",    # Should be ACTIVE (ends in 0)
        "123451",    # Should be ACTIVE (ends in 1)
        "123453",    # Should be INACTIVE (ends in 3)
    ]
    
    print("Testing enhanced chatbot with policy numbers:")
    print("=" * 60)
    
    for policy_num in test_cases:
        print(f"\nTesting policy number: {policy_num}")
        response = service.process_message(policy_num, "test_session")
        print(f"Response: {response['text']}")
        print(f"Intent: {response.get('intent', 'N/A')}")
        print(f"Requires followup: {response.get('requires_followup', False)}")
        if response.get('followup_question'):
            print(f"Followup: {response['followup_question']}")
    
    # Test with greeting
    print(f"\nTesting greeting:")
    response = service.process_message("Hello", "test_session")
    print(f"Response: {response['text']}")
    print(f"Intent: {response.get('intent', 'N/A')}")

if __name__ == "__main__":
    test_chatbot()