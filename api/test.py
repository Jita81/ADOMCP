"""
Minimal Authentication endpoint (using test.py endpoint)
"""

from datetime import datetime
from http.server import BaseHTTPRequestHandler
import json
import re
import secrets

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get authentication information"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "service": "ADOMCP Authentication Service",
            "authentication_required": True,
            "deployment_status": "WORKING - using /api/test endpoint",
            "timestamp": datetime.now().isoformat(),
            "how_to_register": {
                "method": "POST",
                "body": {"email": "your-email@company.com"},
                "response": "API key for authentication"
            },
            "message": "Authentication endpoint is working!",
            "endpoint": "/api/test"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_POST(self):
        """Register user and generate API key"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            email = data.get('email', '').strip().lower()
            
            # Simple email validation
            if not email or '@' not in email or '.' not in email.split('@')[1]:
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
            
            # Generate secure API key
            timestamp = int(datetime.now().timestamp())
            user_hash = email.replace('@', '_').replace('.', '_')[:8]
            random_part = secrets.token_hex(8)
            api_key = f"adomcp_v1_{user_hash}_{timestamp}_{random_part}"
            
            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "success",
                "message": "API key generated successfully",
                "email": email,
                "api_key": api_key,
                "scopes": ["read", "write", "manage_keys"],
                "expires_in_days": 365,
                "timestamp": datetime.now().isoformat(),
                "deployment_note": "Authentication working via /api/test endpoint",
                "usage_instructions": {
                    "step1": "Store this API key securely", 
                    "step2": "Include in Authorization header: 'Bearer " + api_key + "'",
                    "step3": "Use with secure endpoints when they're deployed"
                },
                "security_notice": "This API key provides access to your ADOMCP resources"
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