"""
Secure MCP JSON-RPC endpoint with authentication
Replaces the insecure MCP endpoint with proper user authentication
"""

import json
import sys
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler

# Add security module to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from security import (SecurityValidator, check_rate_limit, get_security_headers)
from security.authentication import authenticate_api_request, validate_user_access

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get secure MCP information"""
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
        
        response = {
            "service": "Secure Azure DevOps Multi-Platform MCP",
            "protocol": "JSON-RPC 2.0",
            "version": "2.2.0",
            "authentication_required": True,
            "methods": ["tools/list", "tools/call"],
            "timestamp": datetime.now().isoformat(),
            "correlation_id": correlation_id,
            "security_features": [
                "API key authentication",
                "User isolation", 
                "Scope-based authorization",
                "Rate limiting",
                "Audit logging"
            ],
            "how_to_authenticate": {
                "step1": "Get API key from POST /api/auth",
                "step2": "Include in Authorization header: 'Bearer <your-api-key>'",
                "step3": "Send JSON-RPC requests to this endpoint"
            },
            "example_request": {
                "headers": {
                    "Authorization": "Bearer adomcp_v1_<your-api-key>",
                    "Content-Type": "application/json"
                },
                "body": {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 1
                }
            },
            "note": "All operations now require authentication and are isolated per user"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_POST(self):
        """Handle secure MCP JSON-RPC requests"""
        # Initialize security
        validator = SecurityValidator()
        correlation_id = validator.generate_correlation_id()
        
        # Add security headers
        for header, value in get_security_headers().items():
            self.send_header(header, value)
        
        try:
            content_length = int(self.headers['Content-Length'])
            
            # Rate limiting
            client_ip = self.client_address[0]
            user_agent = self.headers.get('User-Agent', '')
            
            rate_ok, rate_info = check_rate_limit(client_ip, self.path, user_agent, content_length)
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
                
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32001,
                        "message": "Authentication required",
                        "data": {
                            "required_header": "Authorization: Bearer <your-api-key>",
                            "how_to_get_key": "POST to /api/auth with your email"
                        }
                    },
                    "id": None,
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            api_key = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Authenticate request
            is_valid, authenticated_user, auth_error = authenticate_api_request(api_key, 'write')
            if not is_valid:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32002,
                        "message": "Authentication failed",
                        "data": auth_error
                    },
                    "id": None,
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            # Validate request size
            size_ok, size_error = validator.validate_request_size(content_length)
            if not size_ok:
                self.send_response(413)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32003,
                        "message": "Request too large",
                        "data": {"error": size_error}
                    },
                    "id": None,
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            # Validate MCP JSON-RPC request
            mcp_valid, mcp_error = validator.validate_mcp_request(body)
            if not mcp_valid:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32602,
                        "message": f"Invalid MCP request: {mcp_error}"
                    },
                    "id": body.get('id'),
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            method_name = body.get('method')
            params = body.get('params', {})
            request_id = body.get('id')
            
            if method_name == "tools/list":
                tools = [
                    {
                        "name": "create_work_item",
                        "description": "Create a new work item in Azure DevOps, GitHub, or GitLab (authenticated)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "platform": {"type": "string", "enum": ["azure_devops", "github", "gitlab"]},
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "work_item_type": {"type": "string"}
                            },
                            "required": ["platform", "title", "work_item_type"]
                        }
                    },
                    {
                        "name": "update_work_item",
                        "description": "Update an existing work item (authenticated)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "platform": {"type": "string", "enum": ["azure_devops", "github", "gitlab"]},
                                "work_item_id": {"type": "integer"},
                                "updates": {"type": "object"}
                            },
                            "required": ["platform", "work_item_id", "updates"]
                        }
                    },
                    {
                        "name": "upload_attachment",
                        "description": "Upload a document and attach it to a work item (authenticated)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "work_item_id": {"type": "integer"},
                                "content": {"type": "string"},
                                "filename": {"type": "string"},
                                "project": {"type": "string"}
                            },
                            "required": ["work_item_id", "content", "filename", "project"]
                        }
                    }
                ]
                
                response_body = {
                    "jsonrpc": "2.0",
                    "result": {
                        "tools": tools,
                        "authenticated_user": authenticated_user,
                        "security_notice": "All operations are isolated to your account"
                    },
                    "id": request_id,
                    "correlation_id": correlation_id
                }
                
            elif method_name == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                if tool_name == "create_work_item":
                    result = {
                        "status": "success",
                        "message": f"Work item '{tool_args.get('title', 'Unknown')}' would be created for user {authenticated_user}",
                        "authenticated_user": authenticated_user,
                        "simulated": True,
                        "timestamp": datetime.now().isoformat(),
                        "security": "This operation is isolated to your account",
                        "note": "Real implementation would use your stored platform API keys"
                    }
                elif tool_name == "update_work_item":
                    result = {
                        "status": "success", 
                        "message": f"Work item #{tool_args.get('work_item_id', 'Unknown')} would be updated for user {authenticated_user}",
                        "authenticated_user": authenticated_user,
                        "simulated": True,
                        "timestamp": datetime.now().isoformat(),
                        "security": "This operation is isolated to your account",
                        "note": "Real implementation would use your stored platform API keys"
                    }
                elif tool_name == "upload_attachment":
                    result = {
                        "status": "success",
                        "message": f"Attachment '{tool_args.get('filename', 'Unknown')}' would be uploaded for user {authenticated_user}",
                        "authenticated_user": authenticated_user,
                        "simulated": True,
                        "timestamp": datetime.now().isoformat(),
                        "security": "This operation is isolated to your account",
                        "note": "Real implementation would use your stored platform API keys"
                    }
                else:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('X-Correlation-ID', correlation_id)
                    self.end_headers()
                    
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": f"Tool '{tool_name}' not found"
                        },
                        "id": request_id
                    }
                    self.wfile.write(json.dumps(error_response).encode())
                    return
                
                response_body = {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id,
                    "correlation_id": correlation_id
                }
            
            else:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method_name}' not found"
                    },
                    "id": request_id
                }
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Correlation-ID', correlation_id)
            self.end_headers()
            self.wfile.write(json.dumps(response_body).encode())
            return
            
        except json.JSONDecodeError as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Correlation-ID', correlation_id)
            self.end_headers()
            
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error: Invalid JSON"
                },
                "id": None,
                "correlation_id": correlation_id
            }
            self.wfile.write(json.dumps(error_response).encode())
            return
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Correlation-ID', correlation_id)
            self.end_headers()
            
            # Create safe error response
            safe_response = validator.create_safe_error_response(e, correlation_id, "Secure MCP JSON-RPC")
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32000,
                    "message": safe_response["error"]
                },
                "id": None,
                "correlation_id": correlation_id
            }
            self.wfile.write(json.dumps(error_response).encode())
            return
