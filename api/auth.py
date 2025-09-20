"""
Authentication Registration Endpoint
Allows users to register and get their ADOMCP API keys
"""

import json
import os
import sys
import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import urllib.parse

# Add security module to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from security import SecurityValidator, check_rate_limit, get_security_headers
from security.authentication import auth_manager, generate_user_api_key

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get authentication information"""
        # Initialize security
        validator = SecurityValidator()
        correlation_id = validator.generate_correlation_id()
        
        # Add security headers
        for header, value in get_security_headers().items():
            self.send_header(header, value)
        
        # Rate limiting
        client_ip = self.client_address[0]
        user_agent = self.headers.get('User-Agent', '')
        
        rate_ok, rate_info = check_rate_limit(client_ip, self.path, user_agent, 0)
        if not rate_ok:
            self.send_response(429)
            self.send_header('Content-type', 'application/json')
            self.send_header('Retry-After', str(rate_info.get('retry_after', 60)))
            self.send_header('X-Correlation-ID', correlation_id)
            self.end_headers()
            self.wfile.write(json.dumps(rate_info).encode())
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('X-Correlation-ID', correlation_id)
        self.end_headers()
        
        auth_info = auth_manager.get_authentication_info()
        
        response = {
            "service": "ADOMCP Authentication Service",
            "authentication_required": True,
            "how_to_register": {
                "step1": "POST to /api/auth with your email address",
                "step2": "Receive your secure API key",
                "step3": "Use API key in Authorization header: 'Bearer <your-api-key>'"
            },
            "endpoints": {
                "register": "POST /api/auth",
                "secure_keys": "GET/POST /api/secure-keys (requires auth)",
                "secure_mcp": "POST /api/secure-mcp (requires auth)"
            },
            "authentication_info": auth_info,
            "timestamp": datetime.now().isoformat(),
            "correlation_id": correlation_id,
            "security_notice": "This system now requires authentication to prevent unauthorized access"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_POST(self):
        """Register user and generate API key"""
        # Initialize security
        validator = SecurityValidator()
        correlation_id = validator.generate_correlation_id()
        
        # Add security headers
        for header, value in get_security_headers().items():
            self.send_header(header, value)
        
        try:
            content_length = int(self.headers['Content-Length'])
            
            # Strict rate limiting for registration
            client_ip = self.client_address[0]
            user_agent = self.headers.get('User-Agent', '')
            
            rate_ok, rate_info = check_rate_limit(client_ip, '/register' + self.path, user_agent, content_length)
            if not rate_ok:
                self.send_response(429)
                self.send_header('Content-type', 'application/json')
                self.send_header('Retry-After', str(rate_info.get('retry_after', 60)))
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                self.wfile.write(json.dumps(rate_info).encode())
                return
            
            # Validate request size
            size_ok, size_error = validator.validate_request_size(content_length)
            if not size_ok:
                self.send_response(413)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                response = {"error": size_error, "correlation_id": correlation_id}
                self.wfile.write(json.dumps(response).encode())
                return
            
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Validate required fields
            if 'email' not in data:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                response = {
                    "error": "Missing required field: email",
                    "example": {
                        "email": "your-email@company.com",
                        "purpose": "Brief description of intended use (optional)"
                    },
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            email = data['email'].strip().lower()
            purpose = data.get('purpose', 'ADOMCP API access')
            
            # Validate email format
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                response = {
                    "error": "Invalid email format",
                    "email_provided": email,
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Check if user already has an API key
            existing_keys = auth_manager.list_user_keys(email)
            if existing_keys:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                response = {
                    "status": "already_registered",
                    "message": "You already have API keys registered",
                    "email": email,
                    "existing_keys": len(existing_keys),
                    "note": "Use your existing API key. If you've lost it, contact support.",
                    "correlation_id": correlation_id,
                    "timestamp": datetime.now().isoformat()
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Generate new API key for user
            scopes = ['read', 'write', 'manage_keys']
            api_key = generate_user_api_key(email, scopes)
            
            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Correlation-ID', correlation_id)
            self.end_headers()
            
            response = {
                "status": "success",
                "message": "API key generated successfully",
                "email": email,
                "api_key": api_key,
                "scopes": scopes,
                "expires_in_days": 365,
                "usage_instructions": {
                    "step1": "Store this API key securely (it won't be shown again)",
                    "step2": "Include in Authorization header: 'Bearer " + api_key + "'",
                    "step3": "Access secure endpoints like /api/secure-keys and /api/secure-mcp"
                },
                "security_notice": "Keep your API key secure. It provides access to your ADOMCP resources.",
                "correlation_id": correlation_id,
                "timestamp": datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(response).encode())
            return
            
        except json.JSONDecodeError as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Correlation-ID', correlation_id)
            self.end_headers()
            
            safe_response = validator.create_safe_error_response(e, correlation_id, "JSON parsing")
            safe_response["error"] = "Invalid JSON in request body"
            self.wfile.write(json.dumps(safe_response).encode())
            return
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Correlation-ID', correlation_id)
            self.end_headers()
            
            safe_response = validator.create_safe_error_response(e, correlation_id, "User registration")
            self.wfile.write(json.dumps(safe_response).encode())
            return
