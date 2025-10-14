#!/usr/bin/env python3
"""
Ultra-simple HTTP server for insurance verification
Now with Google Gemini-powered chatbot integration
"""

import json
import uuid
import re
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# Try to import Google Generative AI library
try:
    import google.generativeai as genai
    
    # Configure Gemini API (use environment variable or a placeholder)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Set up the model
    gemini_model = genai.GenerativeModel('gemini-pro')
except ImportError:
    print("Google Generative AI library not installed. Chatbot will use fallback responses.")
    genai = None
    gemini_model = None

# In-memory storage
verifications = {}
chat_sessions = {}
policies_db = {
    "432345": {
        "policy_number": "432345",
        "provider": "State Life",
        "member_id": "17600999012345",
        "name": "John Smith",
        "type": "Health",
        "status": "ACTIVE",
        "expiry_date": "2026-10-10",
        "coverage": "$500,000",
        "premium": "$250/month",
        "date_of_birth": "1985-05-15"
    },
    "123456": {
        "policy_number": "123456",
        "provider": "National Insurance",
        "member_id": "17600999054321",
        "name": "Jane Doe",
        "type": "Auto",
        "status": "ACTIVE",
        "expiry_date": "2025-12-31",
        "coverage": "$100,000",
        "premium": "$150/month",
        "date_of_birth": "1990-08-22"
    },
    "789012": {
        "policy_number": "789012",
        "provider": "Home Secure",
        "member_id": "17600999067890",
        "name": "Robert Johnson",
        "type": "Home",
        "status": "ACTIVE",
        "expiry_date": "2027-06-15",
        "coverage": "$750,000",
        "premium": "$300/month",
        "date_of_birth": "1975-11-30"
    }
}

class InsuranceHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/':
            response = {"message": "Insurance Verification System API", "status": "healthy"}
        elif path == '/health':
            response = {"status": "healthy", "version": "1.0.0", "environment": "development"}
        elif path == '/api/policies':
            # Return all saved policies for the Saved Policies modal
            response = {
                "policies": list(policies_db.values())
            }
        elif path == '/api/policy-info/by-number':
            # Frontend chatbot uses this endpoint to look up policy numbers
            query_params = parse_qs(parsed_url.query)
            raw_number = (query_params.get('policyNumber') or [None])[0]
            
            # Extract 6+ digit policy number safely
            policy_match = re.findall(r'\b\d{6,}\b', raw_number or '')
            policy_number = policy_match[0] if policy_match else None
            
            if not policy_number:
                # Mimic FastAPI not-found behavior but keep 200 for this simple server
                response = {
                    "policy_number": raw_number,
                    "coverage_status": "not_found",
                    "expiry_date": None,
                    "source": "direct",
                    "message": f"Policy number {raw_number} was not found in our records. Could you please double-check the number again?"
                }
            else:
                # Determine status based on last digit (testing logic)
                last_digit = int(policy_number[-1]) if policy_number[-1].isdigit() else 0
                if last_digit in [0, 1, 2]:
                    status = "active"
                    expiry = "2024-12-31"
                    premium_status = "paid"
                    coverage_amount = "$50,000"
                elif last_digit in [3, 4, 5]:
                    status = "inactive"
                    expiry = "2023-06-15"
                    premium_status = "overdue"
                    coverage_amount = "$0"
                elif last_digit in [6, 7, 8]:
                    status = "expired"
                    expiry = "2023-01-01"
                    premium_status = "overdue"
                    coverage_amount = "$0"
                else:
                    status = "pending"
                    expiry = "2024-03-30"
                    premium_status = "under_review"
                    coverage_amount = "TBD"
                
                providers = ["State Life", "EFU", "Jubilee", "Adamjee", "IGI"]
                provider_index = int(policy_number) % len(providers)
                provider_name = providers[provider_index]
                
                response = {
                    "policy_number": policy_number,
                    "coverage_status": status,
                    "expiry_date": expiry,
                    "source": "direct",
                    "provider_name": provider_name,
                    "coverage_amount": coverage_amount,
                    "premium_status": premium_status,
                    "member_name": f"Customer {policy_number}"
                }
        elif path.startswith('/api/policies/'):
            # Get individual policy by ID
            policy_id = path.split('/')[-1]
            if policy_id in policies_db:
                response = policies_db[policy_id]
            else:
                response = {"error": "Policy not found"}
        else:
            response = {"error": "Not found"}
        
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode()) if post_data else {}
        except json.JSONDecodeError:
            data = {}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if self.path == '/api/verify':
            response = self.handle_verify(data)
        elif self.path == '/api/policy-info':
            response = self.handle_policy_info(data)
        elif self.path == '/api/chat':
            response = self.handle_chat(data)
        elif self.path == '/api/chat/session':
            response = self.handle_create_session()
        elif self.path == '/api/policies':
            response = self.handle_create_policy(data)
        else:
            response = {"error": "Endpoint not found"}

        self.wfile.write(json.dumps(response).encode())
        
    def do_PUT(self):
        """Handle PUT requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        put_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(put_data.decode()) if put_data else {}
        except json.JSONDecodeError:
            data = {}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path.startswith('/api/policies/'):
            # Update policy by ID
            policy_id = path.split('/')[-1]
            if policy_id in policies_db:
                # Update the policy with new data
                policy = policies_db[policy_id]
                for key, value in data.items():
                    policy[key] = value
                policy['updated_at'] = datetime.now().isoformat()
                policies_db[policy_id] = policy
                response = policy
            else:
                response = {"error": "Policy not found"}
        else:
            response = {"error": "Endpoint not found"}

        self.wfile.write(json.dumps(response).encode())
        
    def do_DELETE(self):
        """Handle DELETE requests"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path.startswith('/api/policies/'):
            # Delete policy by ID
            policy_id = path.split('/')[-1]
            if policy_id in policies_db:
                # Delete the policy
                deleted_policy = policies_db.pop(policy_id)
                response = {"success": True, "message": "Policy deleted successfully", "policy": deleted_policy}
            else:
                response = {"error": "Policy not found"}
        else:
            response = {"error": "Endpoint not found"}

        self.wfile.write(json.dumps(response).encode())

    def handle_verify(self, data):
        """Handle insurance verification with realistic scenarios"""
        request_id = str(uuid.uuid4())
        member_id = data.get('member_id', '')
        provider = data.get('provider', 'unknown')
        dob = data.get('dob', '')
        last_name = data.get('last_name', '')
        
        # Simulate different scenarios based on member ID patterns
        if not member_id or len(member_id) < 6:
            return {
                "request_id": request_id,
                "status": "error",
                "error_code": "INVALID_MEMBER_ID",
                "message": "Member ID must be at least 6 characters long",
                "verified_at": datetime.now().isoformat()
            }
        
        # Determine scenario based on member ID
        last_digit = int(member_id[-1]) if member_id[-1].isdigit() else 0
        
        if last_digit in [0, 1, 2]:  # 30% chance - Active policy
            status = "active"
            expiry_date = "2025-12-31"
            premium_status = "paid"
            coverage_amount = "$50,000"
            message = "Policy is active and in good standing"
        elif last_digit in [3, 4]:  # 20% chance - Expired policy
            status = "expired"
            expiry_date = "2024-06-15"
            premium_status = "overdue"
            coverage_amount = "$0"
            message = "Policy has expired. Please contact your agent to renew"
        elif last_digit in [5, 6]:  # 20% chance - Suspended policy
            status = "suspended"
            expiry_date = "2025-03-31"
            premium_status = "overdue"
            coverage_amount = "$0"
            message = "Policy is suspended due to non-payment of premiums"
        elif last_digit == 7:  # 10% chance - Policy not found
            return {
                "request_id": request_id,
                "status": "not_found",
                "error_code": "POLICY_NOT_FOUND",
                "message": f"No policy found for member ID {member_id} with {provider}",
                "verified_at": datetime.now().isoformat()
            }
        elif last_digit == 8:  # 10% chance - Pending verification
            status = "pending_verification"
            expiry_date = "2025-12-31"
            premium_status = "under_review"
            coverage_amount = "TBD"
            message = "Policy verification is pending. Please allow 24-48 hours for processing"
        else:  # 10% chance - Grace period
            status = "grace_period"
            expiry_date = "2025-01-15"
            premium_status = "grace_period"
            coverage_amount = "$50,000"
            message = "Policy is in grace period. Payment required within 30 days"
        
        policy_number = f"POL{provider.upper()[:3]}{member_id[:6]}"
        
        mock_response = {
            "policy_number": policy_number,
            "member_id": member_id,
            "member_name": f"{last_name.title()}, John",
            "provider": provider.title(),
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
            "provider": provider,
            "member_id": member_id,
            "verified_at": datetime.now().isoformat(),
            "response": mock_response
        }
        
        return {
            "request_id": request_id,
            "status": "verified" if status in ["active", "expired", "suspended", "grace_period", "pending_verification"] else "not_found",
            "verified_at": datetime.now().isoformat(),
            "source": "provider_api",
            "provider_response": mock_response
        }

    def handle_policy_info(self, data):
        """Handle policy info request with realistic data"""
        member_id = data.get('member_id', '')
        
        if not member_id:
            return {
                "error": "Member ID is required",
                "error_code": "MISSING_MEMBER_ID"
            }
        
        # Use same logic as verification for consistency
        last_digit = int(member_id[-1]) if member_id and member_id[-1].isdigit() else 0
        
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
                "member_id": member_id
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
            "policy_number": f"POL{member_id[:6].upper()}",
            "member_id": member_id,
            "coverage_status": status,
            "expiry_date": expiry_date,
            "premium_status": premium_status,
            "coverage_amount": coverage_amount,
            "plan_type": "Health Insurance Premium",
            "source": "policy_database",
            "verified_at": datetime.now().isoformat(),
            "next_payment_due": "2025-02-01" if status in ["active", "grace_period"] else None
        }

    def handle_chat(self, data):
        """Handle chat request with Gemini-powered intelligence"""
        session_id = data.get('session_id') or str(uuid.uuid4())
        message = data.get('message', '')
        
        # Extract policy numbers from message (6-digit numbers)
        policy_numbers = re.findall(r'\b\d{6}\b', message)
        policy_number = policy_numbers[0] if policy_numbers else None
        
        # If policy number is found but not in database, generate it dynamically
        if policy_number and policy_number not in policies_db:
            # Generate a random policy for any 6-digit number
            policies_db[policy_number] = {
                "policy_number": policy_number,
                "provider": "Universal Insurance",
                "member_id": f"1760{policy_number}",
                "name": f"Customer {policy_number[:3]}",
                "type": "Health",
                "status": "ACTIVE",
                "expiry_date": "2026-12-31",
                "coverage": "$250,000",
                "premium": "$200/month",
                "date_of_birth": "1980-01-01"
            }
        
        # Check for add/create intent
        is_add_intent = any(word in message.lower() for word in ["add", "create", "new"]) and "policy" in message.lower()
        
        # Store chat context in session
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                "session_id": session_id,
                "messages": [],
                "context": {},
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
        
        # Update session
        chat_sessions[session_id]["messages"].append({"role": "user", "content": message})
        chat_sessions[session_id]["last_activity"] = datetime.now().isoformat()
        
        # Check if we're in the middle of creating a policy
        is_creating_policy = chat_sessions[session_id].get("context", {}).get("creating_policy", False)
        
        # Process with Gemini if available
        if gemini_model and GEMINI_API_KEY != "YOUR_API_KEY_HERE":
            # Handle policy creation flow
            if is_creating_policy:
                # Process the user's response to policy creation prompts
                policy_data = chat_sessions[session_id]["context"].get("policy_data", {})
                
                # Extract policy information from the message
                if "name" in message.lower() and not policy_data.get("first_name"):
                    # Extract name (assuming format like "Name: John Doe" or just "John Doe")
                    name_match = re.search(r'name:?\s*([a-zA-Z\s]+)', message, re.IGNORECASE)
                    if name_match:
                        full_name = name_match.group(1).strip().split()
                    else:
                        # Try to extract just a name without label
                        name_parts = [word for word in message.split() if word[0].isupper() and word.isalpha()]
                        if len(name_parts) >= 2:
                            full_name = name_parts[:2]  # Take first two capitalized words as name
                        else:
                            full_name = []
                    
                    if len(full_name) >= 2:
                        policy_data["first_name"] = full_name[0]
                        policy_data["last_name"] = " ".join(full_name[1:])
                
                # Extract provider
                if "provider" in message.lower() and not policy_data.get("provider"):
                    provider_match = re.search(r'provider:?\s*([a-zA-Z\s]+)', message, re.IGNORECASE)
                    if provider_match:
                        policy_data["provider"] = provider_match.group(1).strip()
                
                # Extract date of birth
                if ("birth" in message.lower() or "dob" in message.lower()) and not policy_data.get("date_of_birth"):
                    dob_match = re.search(r'(birth|dob):?\s*([\d\/\-\.]+)', message, re.IGNORECASE)
                    if dob_match:
                        policy_data["date_of_birth"] = dob_match.group(2).strip()
                
                # Extract coverage amount
                if "coverage" in message.lower() and not policy_data.get("coverage_amount"):
                    coverage_match = re.search(r'coverage:?\s*(\$?[\d,]+)', message, re.IGNORECASE)
                    if coverage_match:
                        amount = coverage_match.group(1).strip()
                        if not amount.startswith('$'):
                            amount = f"${amount}"
                        policy_data["coverage_amount"] = amount
                
                # Extract premium
                if "premium" in message.lower() and not policy_data.get("premium"):
                    premium_match = re.search(r'premium:?\s*(\$?[\d,]+\/?(month|mo|year|yr)?)', message, re.IGNORECASE)
                    if premium_match:
                        premium = premium_match.group(1).strip()
                        if not premium.startswith('$'):
                            premium = f"${premium}"
                        if not any(period in premium.lower() for period in ['/month', '/mo', '/year', '/yr']):
                            premium = f"{premium}/month"
                        policy_data["premium"] = premium
                
                # Extract expiry date
                if ("expiry" in message.lower() or "expiration" in message.lower()) and not policy_data.get("expiry_date"):
                    expiry_match = re.search(r'(expiry|expiration):?\s*([\d\/\-\.]+)', message, re.IGNORECASE)
                    if expiry_match:
                        policy_data["expiry_date"] = expiry_match.group(2).strip()
                
                # Update the context with the extracted data
                chat_sessions[session_id]["context"]["policy_data"] = policy_data
                
                # Check if we have all required fields
                required_fields = ["first_name", "last_name", "provider", "coverage_amount", "premium", "expiry_date"]
                missing_fields = [field for field in required_fields if not policy_data.get(field)]
                
                if not missing_fields:
                    # All required fields are provided, create the policy
                    member_id = policy_data.get("member_id", f"{random.randint(100000, 999999)}")
                    
                    # Create the policy
                    new_policy = self.handle_create_policy({
                        "first_name": policy_data.get("first_name"),
                        "last_name": policy_data.get("last_name"),
                        "provider": policy_data.get("provider"),
                        "date_of_birth": policy_data.get("date_of_birth", ""),
                        "coverage_amount": policy_data.get("coverage_amount"),
                        "premium": policy_data.get("premium"),
                        "expiry_date": policy_data.get("expiry_date"),
                        "member_id": member_id
                    })
                    
                    # Reset the context
                    chat_sessions[session_id]["context"]["creating_policy"] = False
                    chat_sessions[session_id]["context"]["policy_data"] = {}
                    
                    # Generate response with Gemini
                    try:
                        prompt = f"""
                        You are an insurance assistant chatbot. The user has provided all the required information to create a new policy.
                        
                        A new policy has been created with the following details:
                        Name: {new_policy.get('first_name', '')} {new_policy.get('last_name', '')}
                        Policy Number: {new_policy.get('policy_number', '')}
                        Member ID: {new_policy.get('member_id', '')}
                        Provider: {new_policy.get('provider', '')}
                        Coverage Amount: {new_policy.get('coverage_amount', '')}
                        Premium: {new_policy.get('premium', '')}
                        Plan Expiry Date: {new_policy.get('expiry_date', '')}
                        
                        Please respond with a confirmation message in a conversational tone, confirming that the policy has been created successfully.
                        """
                        
                        gemini_response = gemini_model.generate_content(prompt)
                        response = gemini_response.text
                    except Exception as e:
                        print(f"Gemini API error: {e}")
                        response = f"Got it! The new policy for member {member_id} has been successfully added. The policy number is {new_policy.get('policy_number')}."
                    
                    intent = "policy_created"
                else:
                    # Still missing some fields, ask for them
                    try:
                        prompt = f"""
                        You are an insurance assistant chatbot. The user is in the process of creating a new policy.
                        
                        So far, I have collected the following information:
                        {', '.join([f"{field.replace('_', ' ').title()}: {policy_data.get(field)}" for field in required_fields if policy_data.get(field)])}
                        
                        I still need the following information:
                        {', '.join([field.replace('_', ' ').title() for field in missing_fields])}
                        
                        Please generate a polite message asking the user to provide the missing information.
                        """
                        
                        gemini_response = gemini_model.generate_content(prompt)
                        response = gemini_response.text
                    except Exception as e:
                        print(f"Gemini API error: {e}")
                        response = f"Thanks for providing that information. I still need the following details to create the policy:\n\n" + "\n".join([field.replace('_', ' ').title() for field in missing_fields])
                    
                    intent = "create_policy_followup"
            
            elif policy_number:
                # Look up policy in database
                policy_data = None
                for policy in policies_db.values():
                    if policy.get("member_id") == policy_number or policy.get("policy_number") == policy_number:
                        policy_data = policy
                        break
                
                if policy_data:
                    # Format policy data for Gemini
                    policy_context = f"""
                    Policy found with the following details:
                    Name: {policy_data.get('first_name', '')} {policy_data.get('last_name', '')}
                    Policy Number: {policy_data.get('policy_number', '')}
                    Member ID: {policy_data.get('member_id', '')}
                    Provider: {policy_data.get('provider', '')}
                    Coverage Amount: {policy_data.get('coverage_amount', '')}
                    Premium Status: {policy_data.get('premium_status', '')}
                    Plan Expiry Date: {policy_data.get('expiry_date', '')}
                    """
                    
                    # Create prompt for Gemini
                    prompt = f"""
                    You are an insurance assistant chatbot. The user has asked: "{message}"
                    
                    I found the following policy information:
                    {policy_context}
                    
                    Please respond with a clear, natural summary of this policy information in a conversational tone.
                    Format the response nicely with appropriate line breaks.
                    """
                    
                    try:
                        gemini_response = gemini_model.generate_content(prompt)
                        response = gemini_response.text
                        intent = "policy_lookup"
                    except Exception as e:
                        print(f"Gemini API error: {e}")
                        response = f"I found policy {policy_number}. Here are the details:\nName: {policy_data.get('first_name', '')} {policy_data.get('last_name', '')}\nPolicy Number: {policy_data.get('policy_number', '')}\nProvider: {policy_data.get('provider', '')}\nCoverage Amount: {policy_data.get('coverage_amount', '')}\nPremium Status: {policy_data.get('premium_status', '')}\nExpiry Date: {policy_data.get('expiry_date', '')}"
                        intent = "policy_lookup_fallback"
                else:
                    response = f"I couldn't find a policy or member record for number {policy_number}. Please verify and try again."
                    intent = "policy_not_found"
            
            elif is_add_intent:
                # Handle policy creation intent
                chat_sessions[session_id]["context"]["creating_policy"] = True
                chat_sessions[session_id]["context"]["policy_data"] = {}
                
                if policy_numbers:
                    chat_sessions[session_id]["context"]["policy_data"]["member_id"] = policy_numbers[0]
                
                response = """Sure! Please provide the following details:

Name
Provider
Date of Birth
Coverage Amount
Premium
Plan Expiry Date"""
                intent = "create_policy"
            
            else:
                # General chat with Gemini
                try:
                    # Create prompt for Gemini
                    prompt = f"""
                    You are an insurance assistant chatbot. The user has asked: "{message}"
                    
                    Please respond in a helpful, conversational tone. If the user is asking about policy information,
                    remind them that they can look up a policy by providing a 6-digit policy or member number.
                    If they want to add a new policy, they can say "Add a new policy" or similar.
                    
                    Keep your response concise and focused on insurance-related information.
                    """
                    
                    gemini_response = gemini_model.generate_content(prompt)
                    response = gemini_response.text
                    intent = "general_chat"
                except Exception as e:
                    print(f"Gemini API error: {e}")
                    # Fallback to rule-based responses
                    response = self._get_fallback_response(message)
                    intent = "fallback"
        else:
            # Fallback to rule-based responses if Gemini is not available
            if is_creating_policy:
                # Process the user's response to policy creation prompts
                policy_data = chat_sessions[session_id]["context"].get("policy_data", {})
                
                # Simple parsing of policy information
                if "name" in message.lower():
                    name_parts = re.search(r'name:?\s*([a-zA-Z\s]+)', message, re.IGNORECASE)
                    if name_parts:
                        full_name = name_parts.group(1).strip().split()
                        if len(full_name) >= 2:
                            policy_data["first_name"] = full_name[0]
                            policy_data["last_name"] = " ".join(full_name[1:])
                
                if "provider" in message.lower():
                    provider = re.search(r'provider:?\s*([a-zA-Z\s]+)', message, re.IGNORECASE)
                    if provider:
                        policy_data["provider"] = provider.group(1).strip()
                
                if "birth" in message.lower() or "dob" in message.lower():
                    dob = re.search(r'(birth|dob):?\s*([\d\/\-\.]+)', message, re.IGNORECASE)
                    if dob:
                        policy_data["date_of_birth"] = dob.group(2).strip()
                
                if "coverage" in message.lower():
                    coverage = re.search(r'coverage:?\s*(\$?[\d,]+)', message, re.IGNORECASE)
                    if coverage:
                        amount = coverage.group(1).strip()
                        if not amount.startswith('$'):
                            amount = f"${amount}"
                        policy_data["coverage_amount"] = amount
                
                if "premium" in message.lower():
                    premium = re.search(r'premium:?\s*(\$?[\d,]+\/?(month|mo|year|yr)?)', message, re.IGNORECASE)
                    if premium:
                        premium_val = premium.group(1).strip()
                        if not premium_val.startswith('$'):
                            premium_val = f"${premium_val}"
                        if not any(period in premium_val.lower() for period in ['/month', '/mo', '/year', '/yr']):
                            premium_val = f"{premium_val}/month"
                        policy_data["premium"] = premium_val
                
                if "expiry" in message.lower() or "expiration" in message.lower():
                    expiry = re.search(r'(expiry|expiration):?\s*([\d\/\-\.]+)', message, re.IGNORECASE)
                    if expiry:
                        policy_data["expiry_date"] = expiry.group(2).strip()
                
                # Update the context with the extracted data
                chat_sessions[session_id]["context"]["policy_data"] = policy_data
                
                # Check if we have all required fields
                required_fields = ["first_name", "last_name", "provider", "coverage_amount", "premium", "expiry_date"]
                missing_fields = [field for field in required_fields if not policy_data.get(field)]
                
                if not missing_fields:
                    # All required fields are provided, create the policy
                    member_id = policy_data.get("member_id", f"{random.randint(100000, 999999)}")
                    
                    # Create the policy
                    new_policy = self.handle_create_policy({
                        "first_name": policy_data.get("first_name"),
                        "last_name": policy_data.get("last_name"),
                        "provider": policy_data.get("provider"),
                        "date_of_birth": policy_data.get("date_of_birth", ""),
                        "coverage_amount": policy_data.get("coverage_amount"),
                        "premium": policy_data.get("premium"),
                        "expiry_date": policy_data.get("expiry_date"),
                        "member_id": member_id
                    })
                    
                    # Reset the context
                    chat_sessions[session_id]["context"]["creating_policy"] = False
                    chat_sessions[session_id]["context"]["policy_data"] = {}
                    
                    response = f"Got it! The new policy for member {member_id} has been successfully added. The policy number is {new_policy.get('policy_number')}."
                    intent = "policy_created"
                else:
                    # Still missing some fields, ask for them
                    response = f"Thanks for providing that information. I still need the following details to create the policy:\n\n" + "\n".join([field.replace('_', ' ').title() for field in missing_fields])
                    intent = "create_policy_followup"
            
            elif policy_number:
                # Check if policy exists in database or create it dynamically
                if policy_number not in policies_db:
                    # Generate a random policy for any 6-digit number
                    policies_db[policy_number] = {
                        "policy_number": policy_number,
                        "provider": "Universal Insurance",
                        "member_id": f"1760{policy_number}",
                        "name": f"Customer {policy_number[:3]}",
                        "first_name": f"Customer",
                        "last_name": f"{policy_number[:3]}",
                        "type": "Health",
                        "status": "ACTIVE",
                        "expiry_date": "2026-12-31",
                        "coverage": "$250,000",
                        "coverage_amount": "$250,000",
                        "premium": "$200/month",
                        "premium_status": "Paid",
                        "date_of_birth": "1980-01-01"
                    }
                
                # Get policy data
                policy_data = policies_db[policy_number]
                
                # Format response with policy details
                response = f"I found policy {policy_number}. Here are the details:\nName: {policy_data.get('first_name', '')} {policy_data.get('last_name', '')}\nPolicy Number: {policy_data.get('policy_number', '')}\nProvider: {policy_data.get('provider', '')}\nCoverage Amount: {policy_data.get('coverage_amount', policy_data.get('coverage', ''))}\nPremium Status: {policy_data.get('premium_status', 'Active')}\nExpiry Date: {policy_data.get('expiry_date', '')}"
                intent = "policy_lookup_fallback"
            elif is_add_intent:
                # Handle policy creation intent
                chat_sessions[session_id]["context"]["creating_policy"] = True
                chat_sessions[session_id]["context"]["policy_data"] = {}
                
                if policy_numbers:
                    chat_sessions[session_id]["context"]["policy_data"]["member_id"] = policy_numbers[0]
                
                response = """Sure! Please provide the following details:

Name
Provider
Date of Birth
Coverage Amount
Premium
Plan Expiry Date"""
                intent = "create_policy"
            else:
                response = self._get_fallback_response(message)
                intent = "fallback"
        
        # Store bot response in session
        chat_sessions[session_id]["messages"].append({"role": "assistant", "content": response})
        
        return {
            "response": response,
            "intent": intent,
            "session_id": session_id,
            "requires_followup": intent in ["create_policy", "create_policy_followup"],
            "helpful_actions": self._get_helpful_actions(intent)
        }
        
    def _get_fallback_response(self, message):
        """Get fallback response when Gemini is not available"""
        message = message.lower()
        
        if any(word in message for word in ["hello", "hi", "hey", "start", "begin"]):
            return "Hello! I'm your AI insurance assistant. I can help you with:\n• Policy verification and status checks\n• Coverage details and benefits\n• Premium payment information\n• Claims guidance\n• Policy renewal assistance\n\nWhat would you like to know about your insurance today?"
        elif any(word in message for word in ["policy", "number", "id"]):
            return "I can help you find your policy information. To look up your policy, please provide your 6-digit policy or member number."
        elif any(word in message for word in ["coverage", "covered", "active", "benefits"]):
            return "I can check your coverage status. Please provide your 6-digit policy or member number and I'll give you a quick status update."
        elif any(word in message for word in ["expire", "expiry", "expires", "renewal", "renew"]):
            return "To check your policy expiration date, please provide your 6-digit policy or member number."
        elif any(word in message for word in ["payment", "premium", "pay", "due", "bill"]):
            return "For premium payment information, please provide your 6-digit policy or member number."
        elif any(word in message for word in ["claim", "claims", "file", "accident", "medical"]):
            return "To file an insurance claim, please provide your 6-digit policy or member number first so I can verify your coverage."
        else:
            return "I'm here to help with your insurance needs! I can assist with policy lookups and adding new policies. Please provide a 6-digit policy number to look up information, or say 'Add a new policy' to create one."
    
    def _get_helpful_actions(self, intent):
        """Get helpful action suggestions based on intent"""
        actions = {
            "greeting": ["Check policy status", "Verify coverage", "Payment information"],
            "check_coverage": ["Verify policy", "Contact agent", "Make payment"],
            "payment_info": ["Make payment", "Contact support", "Check policy status"],
            "claims_help": ["Contact provider", "Gather documents", "Check coverage"],
            "testing_help": ["Try verification form", "Test different Member IDs"]
        }
        return actions.get(intent, ["Use verification form", "Contact support"])

    def handle_create_policy(self, data):
        """Handle policy creation request"""
        policy_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Generate a policy number if not provided
        if not data.get("policy_number"):
            import random
            data["policy_number"] = f"POL-{random.randint(100000, 999999)}"
        
        # Generate a member ID if not provided
        if not data.get("member_id"):
            import random
            data["member_id"] = f"{random.randint(100000, 999999)}"
        
        policy_data = {
            "id": policy_id,
            "provider": data.get("provider", ""),
            "member_id": data.get("member_id", ""),
            "policy_number": data.get("policy_number", ""),
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "dob": data.get("dob", ""),
            "email": data.get("email", ""),
            "phone": data.get("phone", ""),
            "address": data.get("address", ""),
            "zip_code": data.get("zip_code", ""),
            "coverage_status": data.get("coverage_status", "active"),
            "expiry_date": data.get("expiry_date", "2025-12-31"),
            "premium_status": data.get("premium_status", "paid"),
            "coverage_amount": data.get("coverage_amount", "$50,000"),
            "premium": data.get("premium", "$0/month"),
            "created_at": now,
            "updated_at": now
        }
        
        # Store the policy in the in-memory database
        policies_db[policy_id] = policy_data
        
        return policy_data
        
    def handle_create_session(self):
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        chat_sessions[session_id] = {
            "session_id": session_id,
            "user_id": "demo-user",
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        return chat_sessions[session_id]

def run_server(port=8000):
    """Run the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, InsuranceHandler)
    print(f"Insurance Verification API Server running on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
