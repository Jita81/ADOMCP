"""
MCP JSON-RPC endpoint for Vercel
"""

import json
from datetime import datetime

def handler(request):
    """Simple Vercel handler for MCP endpoint"""
    method = request.get('httpMethod', 'GET')
    
    if method == 'GET':
        # Return MCP info for GET requests
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {
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
        }
    
    elif method == 'POST':
        # Handle JSON-RPC requests
        try:
            body = json.loads(request.get('body', '{}'))
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
                        "timestamp": datetime.now().isoformat()
                    }
                elif tool_name == "update_work_item":
                    result = {
                        "status": "success", 
                        "message": f"Work item #{tool_args.get('work_item_id', 'Unknown')} would be updated",
                        "simulated": True,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    response_body = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
                        "id": request_id
                    }
                    return {
                        "statusCode": 200,
                        "headers": {"Content-Type": "application/json"},
                        "body": response_body
                    }
                
                response_body = {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id
                }
            
            else:
                response_body = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method '{method_name}' not found"},
                    "id": request_id
                }
            
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": response_body
            }
            
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": {
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": f"Internal error: {str(e)}"},
                    "id": None
                }
            }
    
    else:
        return {
            "statusCode": 405,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {
                "error": "Method not allowed. Use GET for info or POST for JSON-RPC requests."
            }
        }
