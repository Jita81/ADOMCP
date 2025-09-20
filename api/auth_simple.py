"""
Simple authentication endpoint for testing Vercel deployment
No external dependencies to isolate deployment issues
"""

import json
import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get authentication information"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('X-Test-Endpoint', 'auth-simple')
        self.end_headers()
        
        response = {
            "service": "ADOMCP Authentication Service (Simple Test)",
            "status": "deployed",
            "authentication_required": True,
            "test_mode": True,
            "timestamp": datetime.now().isoformat(),
            "message": "This is a simplified auth endpoint for testing deployment",
            "deployment_test": "SUCCESS"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_POST(self):
        """Register user (simplified version)"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('X-Test-Endpoint', 'auth-simple')
        self.end_headers()
        
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
                    "test_mode": True,
                    "timestamp": datetime.now().isoformat()
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Generate simple test API key
            api_key = f"test_key_{email.replace('@', '_').replace('.', '_')}_{int(datetime.now().timestamp())}"
            
            response = {
                "status": "success",
                "message": "Test API key generated (simplified version)",
                "email": email,
                "api_key": api_key,
                "test_mode": True,
                "timestamp": datetime.now().isoformat(),
                "note": "This is a simplified version for testing deployment"
            }
            
            self.wfile.write(json.dumps(response).encode())
            return
            
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "error": "Invalid JSON",
                "test_mode": True,
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
                "test_mode": True,
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
            return
