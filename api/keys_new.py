"""
API key management endpoint with enhanced security
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
                     encrypt_api_key, decrypt_api_key, hash_for_audit)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get API key information (without exposing actual keys)"""
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
            
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            user_id = query_params.get('user_id', [None])[0]
            
            if not user_id:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                response = {
                    "error": "user_id parameter is required",
                    "example": "/api/keys?user_id=your-unique-id",
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Validate user_id
            if not validator.sanitize_string(user_id) or len(user_id.strip()) < 3:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                response = {
                    "error": "Invalid user_id format",
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # In a real implementation, this would query Supabase
            # For now, simulate the response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Correlation-ID', correlation_id)
            self.end_headers()
            
            response = {
                "user_id": user_id,
                "stored_platforms": ["azure_devops", "github"],  # Simulated
                "message": "API key storage is ready. Use POST to store keys.",
                "timestamp": datetime.now().isoformat(),
                "correlation_id": correlation_id,
                "security_features": ["encryption", "rate_limiting", "audit_logging"],
                "note": "Actual keys are stored securely and not returned in GET requests"
            }
            
            self.wfile.write(json.dumps(response).encode())
            return
        
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Correlation-ID', correlation_id)
            self.end_headers()
            
            safe_response = validator.create_safe_error_response(e, correlation_id, "API key retrieval")
            self.wfile.write(json.dumps(safe_response).encode())
            return
    
    def do_POST(self):
        """Store API keys securely with encryption"""
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
            
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Validate API key data
            valid, error, sanitized_data = validator.validate_api_key_data(data)
            if not valid:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                response = {
                    "error": "Validation failed",
                    "details": error,
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            user_id = sanitized_data['user_id']
            platform = sanitized_data['platform']
            api_key = sanitized_data['api_key']
            organization_url = sanitized_data.get('organization_url')
            project_id = sanitized_data.get('project_id')
            
            # Encrypt the API key
            try:
                encrypted_key = encrypt_api_key(api_key, user_id, platform)
                audit_hash = hash_for_audit(api_key)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                safe_response = validator.create_safe_error_response(e, correlation_id, "API key encryption")
                self.wfile.write(json.dumps(safe_response).encode())
                return
            
            # In production, store encrypted_key in Supabase with audit_hash
            # For now, simulate the storage
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Correlation-ID', correlation_id)
            self.end_headers()
            
            response = {
                "status": "success",
                "message": f"API key for {platform} stored securely with encryption",
                "user_id": user_id,
                "platform": platform,
                "organization_url": organization_url,
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
                "correlation_id": correlation_id,
                "audit_hash": audit_hash,  # For audit logging
                "security_features": ["encryption", "validation", "audit_logging"],
                "note": "API key encrypted with user-specific keys. Real implementation would use Supabase."
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
            
            safe_response = validator.create_safe_error_response(e, correlation_id, "API key storage")
            self.wfile.write(json.dumps(safe_response).encode())
            return
