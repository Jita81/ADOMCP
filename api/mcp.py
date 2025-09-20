"""
MCP JSON-RPC endpoint for Vercel
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from mangum import Mangum

app = FastAPI()

# Pydantic models for MCP requests/responses
class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[int] = None

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[int] = None

@app.post("/api/mcp")
async def handle_mcp_request(request: MCPRequest):
    """Handle MCP JSON-RPC requests"""
    try:
        method = request.method
        params = request.params or {}
        
        if method == "tools/list":
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
            return MCPResponse(id=request.id, result={"tools": tools})
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            # Simulate tool execution for demo purposes
            if tool_name == "create_work_item":
                return MCPResponse(
                    id=request.id, 
                    result={
                        "status": "success",
                        "message": f"Work item '{tool_args.get('title', 'Unknown')}' would be created",
                        "simulated": True,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            elif tool_name == "update_work_item":
                return MCPResponse(
                    id=request.id,
                    result={
                        "status": "success", 
                        "message": f"Work item #{tool_args.get('work_item_id', 'Unknown')} would be updated",
                        "simulated": True,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            else:
                return MCPResponse(
                    id=request.id,
                    error={"code": -32601, "message": f"Tool '{tool_name}' not found"}
                )
        
        else:
            return MCPResponse(
                id=request.id,
                error={"code": -32601, "message": f"Method '{method}' not found"}
            )
            
    except Exception as e:
        return MCPResponse(
            id=request.id,
            error={"code": -32000, "message": f"Internal error: {str(e)}"}
        )

@app.get("/api/mcp")
async def mcp_info():
    """Information about the MCP endpoint"""
    return JSONResponse({
        "service": "Azure DevOps Multi-Platform MCP",
        "protocol": "JSON-RPC 2.0",
        "version": "2.2.0",
        "methods": ["tools/list", "tools/call"],
        "timestamp": datetime.now().isoformat(),
        "example_request": {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
    })

@app.get("/")
async def root():
    return await mcp_info()

# Vercel handler
handler = Mangum(app)
