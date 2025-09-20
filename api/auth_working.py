"""
Authentication test endpoint for Vercel (copied from working test.py)
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
            "test_mode": True,
            "timestamp": datetime.now().isoformat(),
            "deployment": "vercel",
            "endpoint": "/api/auth_working",
            "message": "Authentication endpoint working!",
            "status": "success"
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
                    "timestamp": datetime.now().isoformat()
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Generate API key
            api_key = f"adomcp_v1_test_{email.replace('@', '_').replace('.', '_')}_{int(datetime.now().timestamp())}"
            
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
                "test_mode": True,
                "note": "This is a test implementation"
            }
            
            self.wfile.write(json.dumps(response).encode())
            return
            
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "error": "Invalid JSON",
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