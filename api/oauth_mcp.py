"""
OAuth-Protected MCP JSON-RPC Endpoint
Requires OAuth authentication via session token
"""

import json
import sys
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler

# Add security module to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from security.oauth import oauth_manager
from security import SecurityValidator, check_rate_limit, get_security_headers

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get OAuth-protected MCP information"""
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
            "service": "ADOMCP OAuth-Protected MCP",
            "protocol": "JSON-RPC 2.0",
            "version": "3.0.0",
            "authentication": {
                "type": "OAuth",
                "providers": ["GitHub", "Google", "Microsoft"],
                "required": True
            },
            "methods": ["tools/list", "tools/call"],
            "timestamp": datetime.now().isoformat(),
            "correlation_id": correlation_id,
            "security_features": [
                "OAuth authentication",
                "User identity verification",
                "Provider-based authorization",
                "Rate limiting",
                "Session management"
            ],
            "how_to_authenticate": {
                "step1": "Visit /api/oauth/login?provider={github|google|microsoft}",
                "step2": "Complete OAuth flow with your provider",
                "step3": "Copy session token from callback page",
                "step4": "Include in Authorization header: 'Bearer <session-token>'"
            },
            "example_request": {
                "headers": {
                    "Authorization": "Bearer adomcp_oauth_github_...",
                    "Content-Type": "application/json"
                },
                "body": {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 1
                }
            },
            "note": "All operations require OAuth authentication and are isolated per user"
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
        return
    
    def do_POST(self):
        """Handle OAuth-protected MCP JSON-RPC requests"""
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
            
            # Extract OAuth session token from Authorization header
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
                        "message": "OAuth authentication required",
                        "data": {
                            "required_header": "Authorization: Bearer <oauth-session-token>",
                            "how_to_get_token": "Visit /api/oauth/login?provider={github|google|microsoft}",
                            "providers": ["github", "google", "microsoft"]
                        }
                    },
                    "id": None,
                    "correlation_id": correlation_id
                }
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            session_token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Authenticate OAuth request
            is_valid, user_info, auth_error = oauth_manager.authenticate_request(session_token)
            if not is_valid:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Correlation-ID', correlation_id)
                self.end_headers()
                
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32002,
                        "message": "OAuth authentication failed",
                        "data": {
                            "error": auth_error,
                            "how_to_reauth": "Visit /api/oauth/login?provider={provider} to get new token"
                        }
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
                        "description": "Create a new work item in Azure DevOps, GitHub, or GitLab (OAuth authenticated)",
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
                        "description": "Update an existing work item (OAuth authenticated)",
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
                        "description": "Upload a document and attach it to a work item (OAuth authenticated)",
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
                    },
                    {
                        "name": "get_user_profile",
                        "description": "Get authenticated user's profile information",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                ]
                
                response_body = {
                    "jsonrpc": "2.0",
                    "result": {
                        "tools": tools,
                        "authentication": {
                            "type": "OAuth",
                            "user": user_info,
                            "provider": user_info.get('provider', 'unknown')
                        },
                        "security_notice": "All operations are isolated to your authenticated account"
                    },
                    "id": request_id,
                    "correlation_id": correlation_id
                }
                
            elif method_name == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                if tool_name == "get_user_profile":
                    result = {
                        "status": "success",
                        "user_profile": user_info,
                        "session_info": {
                            "authenticated_via": user_info.get('provider', 'unknown'),
                            "user_id": user_info.get('id'),
                            "email": user_info.get('email'),
                            "name": user_info.get('name')
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                elif tool_name == "create_work_item":
                    result = {
                        "status": "success",
                        "message": f"Work item '{tool_args.get('title', 'Unknown')}' would be created for {user_info.get('name', 'user')}",
                        "authenticated_user": user_info,
                        "oauth_provider": user_info.get('provider'),
                        "simulated": True,
                        "timestamp": datetime.now().isoformat(),
                        "security": "This operation is isolated to your OAuth-authenticated account",
                        "note": "Real implementation would use your stored platform credentials"
                    }
                elif tool_name == "update_work_item":
                    result = {
                        "status": "success", 
                        "message": f"Work item #{tool_args.get('work_item_id', 'Unknown')} would be updated for {user_info.get('name', 'user')}",
                        "authenticated_user": user_info,
                        "oauth_provider": user_info.get('provider'),
                        "simulated": True,
                        "timestamp": datetime.now().isoformat(),
                        "security": "This operation is isolated to your OAuth-authenticated account",
                        "note": "Real implementation would use your stored platform credentials"
                    }
                elif tool_name == "upload_attachment":
                    result = {
                        "status": "success",
                        "message": f"Attachment '{tool_args.get('filename', 'Unknown')}' would be uploaded for {user_info.get('name', 'user')}",
                        "authenticated_user": user_info,
                        "oauth_provider": user_info.get('provider'),
                        "simulated": True,
                        "timestamp": datetime.now().isoformat(),
                        "security": "This operation is isolated to your OAuth-authenticated account",
                        "note": "Real implementation would use your stored platform credentials"
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
            self.wfile.write(json.dumps(response_body, indent=2).encode())
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
            safe_response = validator.create_safe_error_response(e, correlation_id, "OAuth MCP JSON-RPC")
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
