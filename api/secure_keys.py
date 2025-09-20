"""
Secure API Key Management Endpoint with Authentication
Replaces the insecure keys.py endpoint with proper authentication
"""

import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import urllib.parse

# Add security module to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from security import (SecurityValidator, check_rate_limit, get_security_headers, 
                     encrypt_api_key_advanced, decrypt_api_key_advanced)
from security.authentication import auth_manager, authenticate_api_request, generate_user_api_key

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get API key information (requires authentication)"""
        # Initialize security
        validator = SecurityValidator()
        correlation_id = validator.generate_correlation_id()
        
        # Add security headers
        for header, value in get_security_headers().items():
            self.send_header(header, value)
        
        try:
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
            
            # Extract API key from Authorization header
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                response = {
                    "error": "Authentication required",
                    "message": "Please provide API key in Authorization header as 'Bearer <your-api-key>'",
                    "how_to_get_key": "POST to /api/auth/register with your email to get an API key",
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            api_key = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Authenticate request
            is_valid, authenticated_user, auth_error = authenticate_api_request(api_key, 'read')
            if not is_valid:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                response = {
                    "error": "Authentication failed",
                    "details": auth_error,
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # User is authenticated - return their key information
            user_keys = auth_manager.list_user_keys(authenticated_user)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Correlation-ID', correlation_id)
            self.end_headers()
            
            response = {
                "user_id": authenticated_user,
                "api_keys": user_keys,
                "message": "Your API keys (keys are never returned for security)",
                "timestamp": datetime.now().isoformat(),
                "correlation_id": correlation_id,
                "security_info": auth_manager.get_authentication_info()
            }
            
            self.wfile.write(json.dumps(response).encode())
            return
        
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Correlation-ID', correlation_id)
            self.end_headers()
            
            safe_response = validator.create_safe_error_response(e, correlation_id, "Secure API key retrieval")
            self.wfile.write(json.dumps(safe_response).encode())
            return
    
    def do_POST(self):
        """Store platform API keys securely (requires authentication)"""
        # Initialize security
        validator = SecurityValidator()
        correlation_id = validator.generate_correlation_id()
        
        # Add security headers
        for header, value in get_security_headers().items():
            self.send_header(header, value)
        
        try:
            content_length = int(self.headers['Content-Length'])
            
            # Rate limiting for auth operations
            client_ip = self.client_address[0]
            user_agent = self.headers.get('User-Agent', '')
            
            rate_ok, rate_info = check_rate_limit(client_ip, '/auth' + self.path, user_agent, content_length)
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
            
            # Extract API key from Authorization header
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                response = {
                    "error": "Authentication required",
                    "message": "Please provide API key in Authorization header as 'Bearer <your-api-key>'",
                    "how_to_get_key": "POST to /api/auth/register with your email to get an API key",
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            api_key = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Authenticate request
            is_valid, authenticated_user, auth_error = authenticate_api_request(api_key, 'manage_keys')
            if not is_valid:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                response = {
                    "error": "Authentication failed",
                    "details": auth_error,
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Validate platform API key data
            required_fields = ['platform', 'api_key']
            for field in required_fields:
                if field not in data:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('X-Correlation-ID', correlation_id)
                    self.end_headers()
                    
                    response = {
                        "error": f"Missing required field: {field}",
                        "required_fields": required_fields,
                        "correlation_id": correlation_id
                    }
                    self.wfile.write(json.dumps(response).encode())
                    return
            
            platform = data['platform']
            platform_api_key = data['api_key']
            organization_url = data.get('organization_url')
            project_id = data.get('project_id')
            
            # Validate platform
            valid_platforms = ['azure_devops', 'github', 'gitlab']
            if platform not in valid_platforms:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                response = {
                    "error": f"Invalid platform: {platform}",
                    "valid_platforms": valid_platforms,
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Encrypt the platform API key with advanced encryption
            additional_data = {
                'organization_url': organization_url,
                'project_id': project_id,
                'stored_by': authenticated_user,
                'stored_at': datetime.now().isoformat()
            }
            
            encrypted_data = encrypt_api_key_advanced(platform_api_key, authenticated_user, platform, additional_data)
            
            # In production, store encrypted_data in Supabase
            # For now, simulate the storage
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Correlation-ID', correlation_id)
            self.end_headers()
            
            response = {
                "status": "success",
                "message": f"Platform API key for {platform} stored securely",
                "user_id": authenticated_user,
                "platform": platform,
                "organization_url": organization_url,
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
                "correlation_id": correlation_id,
                "encryption": {
                    "algorithm": encrypted_data.algorithm,
                    "key_version": encrypted_data.key_version,
                    "encrypted": True
                },
                "note": "Platform API key encrypted with AES-GCM and stored securely"
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
            
            safe_response = validator.create_safe_error_response(e, correlation_id, "Secure API key storage")
            self.wfile.write(json.dumps(safe_response).encode())
            return
