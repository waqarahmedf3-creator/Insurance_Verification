#!/usr/bin/env python3
"""
Ultra-simple HTTP server for insurance verification
No external dependencies required - uses only Python standard library
"""

import json
import uuid
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# In-memory storage
verifications = {}
chat_sessions = {}
policies_db = {}

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
        """Handle chat request with enhanced intelligence"""
        session_id = data.get('session_id') or str(uuid.uuid4())
        message = data.get('message', '').lower()
        member_id = data.get('member_id', '')
        
        # Extract policy numbers from message (6+ digit numbers)
        import re
        policy_numbers = re.findall(r'\b\d{6,}\b', message)
        policy_number = policy_numbers[0] if policy_numbers else None
        
        # Enhanced intent classification with context awareness
        if any(word in message for word in ["hello", "hi", "hey", "start", "begin"]):
            response = "Hello! I'm your AI insurance assistant. I can help you with:\n• Policy verification and status checks\n• Coverage details and benefits\n• Premium payment information\n• Claims guidance\n• Policy renewal assistance\n\nWhat would you like to know about your insurance today?"
            intent = "greeting"
            
        elif policy_number or any(word in message for word in ["policy", "number", "id"]):
            if policy_number:
                # Try to look up policy by the extracted number
                # Convert to member ID format for lookup (use last 6 digits)
                test_member_id = f"test{policy_number[-6:]}"
                last_digit = int(test_member_id[-1]) if test_member_id[-1].isdigit() else 0
                
                if last_digit in [0, 1, 2]:
                    response = f"✅ Great news! I found policy {policy_number}. Your policy is ACTIVE with full coverage of $50,000. Your benefits include medical, dental, and emergency coverage. Policy expires December 31, 2025."
                elif last_digit in [3, 4]:
                    response = f"❌ Policy {policy_number} has EXPIRED as of June 15, 2024. You currently have no active coverage. Please contact your agent immediately to renew your policy."
                elif last_digit in [5, 6]:
                    response = f"⚠️ Policy {policy_number} is SUSPENDED due to non-payment of premiums. Coverage is temporarily unavailable. Please make your premium payment to reactivate your policy."
                elif last_digit == 7:
                    response = f"❌ Policy number {policy_number} was not found in our records. Could you please double-check the policy number and provide it again? Please verify the number is correct and try again."
                elif last_digit == 8:
                    response = f"⏳ Policy {policy_number} is PENDING VERIFICATION. Your policy verification is under review. Please allow 24-48 hours for processing."
                else:
                    response = f"⏳ Policy {policy_number} is in GRACE PERIOD. You have limited coverage until January 15, 2025. Payment is required within 30 days to maintain coverage."
            else:
                response = "I can help you find your policy information. To look up your policy, I'll need:\n• Your Member ID\n• Date of birth\n• Last name\n\nOr provide your 6-digit policy number and I'll check it for you."
            intent = "get_policy_number"
            
        elif any(word in message for word in ["coverage", "covered", "active", "benefits"]):
            if member_id:
                # Simulate policy lookup
                last_digit = int(member_id[-1]) if member_id[-1].isdigit() else 0
                if last_digit in [0, 1, 2]:
                    response = "✅ Good news! Your policy is ACTIVE with full coverage of $50,000. Your benefits include medical, dental, and emergency coverage."
                elif last_digit in [3, 4]:
                    response = "❌ Your policy has EXPIRED as of June 15, 2024. You currently have no active coverage. Please contact your agent immediately to renew."
                elif last_digit in [5, 6]:
                    response = "⚠️ Your policy is SUSPENDED due to non-payment. Coverage is temporarily unavailable. Please make your premium payment to reactivate."
                else:
                    response = "⏳ Your policy is in GRACE PERIOD. You have limited coverage until January 15, 2025. Payment is required within 30 days."
            else:
                response = "I can check your coverage status. Please provide your Member ID using the form above, or tell me your Member ID and I'll give you a quick status update."
            intent = "check_coverage"
            
        elif any(word in message for word in ["expire", "expiry", "expires", "renewal", "renew"]):
            response = "Policy expiration dates vary by status:\n• Active policies: Typically expire December 31st\n• Grace period policies: May have earlier expiration\n• Suspended policies: Coverage suspended until payment\n\nFor your specific expiry date, please use the verification form or provide your Member ID."
            intent = "check_expiry"
            
        elif any(word in message for word in ["payment", "premium", "pay", "due", "bill"]):
            response = "💰 Premium Payment Information:\n• Active policies: Next payment typically due February 1st\n• Overdue accounts: Immediate payment required\n• Grace period: Payment due within 30 days\n\nYou can make payments through your provider's website or by calling customer service."
            intent = "payment_info"
            
        elif any(word in message for word in ["claim", "claims", "file", "accident", "medical"]):
            response = "📋 To file an insurance claim:\n1. Contact your provider within 24-48 hours\n2. Gather all relevant documentation\n3. Fill out claim forms completely\n4. Submit supporting evidence\n\nFor active policies, claims are typically processed within 5-10 business days."
            intent = "claims_help"
            
        elif any(word in message for word in ["contact", "phone", "call", "support", "help"]):
            response = "📞 Contact Information:\n• State Life: 1-800-STATE-LIFE\n• EFU: 1-800-EFU-HELP\n• Jubilee: 1-800-JUBILEE\n\nCustomer service hours: Monday-Friday 8AM-6PM\nEmergency claims: Available 24/7"
            intent = "contact_info"
            
        elif any(word in message for word in ["status", "check", "verify", "lookup"]):
            response = "I can help you check your policy status. Please use the verification form above with:\n• Provider name\n• Member ID\n• Date of birth\n• Last name\n\nThis will give you complete policy details including status, coverage, and expiry information."
            intent = "status_check"
            
        elif "test" in message or any(str(i) in message for i in range(10)):
            # If user mentions test or numbers, give them testing guidance
            response = "🧪 Testing the system? Try these Member IDs to see different scenarios:\n• Ending in 0,1,2: Active policy\n• Ending in 3,4: Expired policy\n• Ending in 5,6: Suspended policy\n• Ending in 7: Policy not found\n• Ending in 8: Pending verification\n• Ending in 9: Grace period\n\nExample: Try Member ID '123450' for an active policy!"
            intent = "testing_help"
            
        else:
            response = "I'm here to help with your insurance needs! I can assist with:\n• Policy verification and status\n• Coverage and benefits information\n• Premium payment details\n• Claims guidance\n• Contact information\n\nPlease ask me about any of these topics, or use the verification form above for detailed policy information."
            intent = "fallback"
        
        return {
            "response": response,
            "intent": intent,
            "session_id": session_id,
            "requires_followup": intent in ["get_policy_number", "check_coverage", "status_check"],
            "helpful_actions": self._get_helpful_actions(intent)
        }
    
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
        """Create a new policy"""
        policy_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
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
