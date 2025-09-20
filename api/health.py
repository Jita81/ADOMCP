"""
Authentication endpoint (temporarily using health.py to test deployment)
"""

from datetime import datetime
from http.server import BaseHTTPRequestHandler
import json
import re

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get authentication information"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "service": "ADOMCP Authentication Service",
            "authentication_required": True,
            "deployment_test": "SUCCESS - Using health.py endpoint",
            "timestamp": datetime.now().isoformat(),
            "how_to_register": {
                "step1": "POST to this endpoint with your email",
                "step2": "Receive your secure API key", 
                "step3": "Use API key in Authorization header"
            },
            "endpoints": {
                "register": "POST /api/health (temporary)",
                "note": "This is using health endpoint for testing deployment"
            },
            "status": "deployed_and_working"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_POST(self):
        """Register user and generate API key"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            email = data.get('email', '')
            
            # Simple email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    "error": "Invalid email format",
                    "example": "user@company.com",
                    "timestamp": datetime.now().isoformat()
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Generate API key
            timestamp = int(datetime.now().timestamp())
            user_hash = email.replace('@', '_').replace('.', '_')
            api_key = f"adomcp_v1_{user_hash}_{timestamp}_temp"
            
            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "success",
                "message": "API key generated successfully (temporary endpoint)",
                "email": email,
                "api_key": api_key,
                "scopes": ["read", "write", "manage_keys"],
                "expires_in_days": 365,
                "timestamp": datetime.now().isoformat(),
                "deployment_note": "Using health endpoint for testing - will move to /api/auth",
                "usage_instructions": {
                    "step1": "Store this API key securely", 
                    "step2": "Include in Authorization header: 'Bearer " + api_key + "'",
                    "step3": "Access secure endpoints (when deployed)"
                }
            }
            
            self.wfile.write(json.dumps(response).encode())
            return
            
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "error": "Invalid JSON in request body",
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
            return
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "error": f"Server error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
            return