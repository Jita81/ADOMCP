"""
MCP JSON-RPC endpoint for Vercel
"""

import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "service": "Azure DevOps Multi-Platform MCP",
            "protocol": "JSON-RPC 2.0",
            "version": "2.2.0",
            "methods": ["tools/list", "tools/call"],
            "timestamp": datetime.now().isoformat(),
            "example_request": {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            },
            "note": "Send POST requests for actual MCP operations"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            body = json.loads(post_data.decode('utf-8'))
            method_name = body.get('method')
            params = body.get('params', {})
            request_id = body.get('id')
            
            if method_name == "tools/list":
                tools = [
                    {
                        "name": "create_work_item",
                        "description": "Create a new work item in Azure DevOps, GitHub, or GitLab",
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
                        "description": "Update an existing work item",
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
                        "description": "Upload a document and attach it to a work item",
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
                    "result": {"tools": tools},
                    "id": request_id
                }
                
            elif method_name == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                if tool_name == "create_work_item":
                    result = {
                        "status": "success",
                        "message": f"Work item '{tool_args.get('title', 'Unknown')}' would be created",
                        "simulated": True,
                        "timestamp": datetime.now().isoformat(),
                        "note": "This is a demo response. Real implementation requires API keys."
                    }
                elif tool_name == "update_work_item":
                    result = {
                        "status": "success", 
                        "message": f"Work item #{tool_args.get('work_item_id', 'Unknown')} would be updated",
                        "simulated": True,
                        "timestamp": datetime.now().isoformat(),
                        "note": "This is a demo response. Real implementation requires API keys."
                    }
                elif tool_name == "upload_attachment":
                    result = {
                        "status": "success",
                        "message": f"Attachment '{tool_args.get('filename', 'Unknown')}' would be uploaded",
                        "simulated": True,
                        "timestamp": datetime.now().isoformat(),
                        "note": "This is a demo response. Real implementation requires API keys."
                    }
                else:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
                        "id": request_id
                    }
                    self.wfile.write(json.dumps(error_response).encode())
                    return
                
                response_body = {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id
                }
            
            else:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method '{method_name}' not found"},
                    "id": request_id
                }
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_body).encode())
            return
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Internal error: {str(e)}"},
                "id": None
            }
            self.wfile.write(json.dumps(error_response).encode())
            return
