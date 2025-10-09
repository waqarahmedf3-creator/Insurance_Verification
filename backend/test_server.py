#!/usr/bin/env python3
"""
Simple test to verify the enhanced chatbot logic
"""

import requests
import json

def test_chatbot():
    """Test the enhanced chatbot with different policy numbers"""
    
    # Test cases with different policy numbers
    test_cases = [
        "123456",    # Should be EXPIRED (ends in 6)
        "123457",    # Should be EXPIRED (ends in 7)
        "123458",    # Should be EXPIRED (ends in 8)
        "123459",    # Should be PENDING (ends in 9)
        "123450",    # Should be ACTIVE (ends in 0)
        "123451",    # Should be ACTIVE (ends in 1)
        "123453",    # Should be INACTIVE (ends in 3)
        "Hello",     # Should be greeting
        "I need help with my policy",  # Should ask for policy number
    ]
    
    print("Testing enhanced chatbot logic:")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/chat"
    
    for test_message in test_cases:
        print(f"\nTesting message: '{test_message}'")
        
        payload = {
            "message": test_message,
            "session_id": "test_session_123"
        }
        
        try:
            response = requests.post(base_url, json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"Response: {result['response']}")
                print(f"Intent: {result['intent']}")
                print(f"Session ID: {result['session_id']}")
                print(f"Requires followup: {result['requires_followup']}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to server. Make sure the server is running.")
            return
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_chatbot()