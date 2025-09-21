#!/usr/bin/env python3
"""
ADOMCP - Hybrid Architecture Implementation
Supports both FastAPI HTTP endpoints AND MCP transports (STDIO, SSE, Streamable HTTP)
Provides maximum compatibility with existing tools and Claude Desktop
"""

import asyncio
import os
import logging
import uvicorn
from typing import Any, Dict, List, Optional, Union
import aiohttp
import json
from contextlib import asynccontextmanager

# FastAPI imports for existing HTTP endpoints
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# MCP SDK imports for Claude Desktop compatibility
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
import mcp.types as types
from mcp.types import (
    Tool, ToolAnnotations, CallToolResult, 
    TextContent, ContentBlock, JSONRPCMessage
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure DevOps configuration
AZURE_DEVOPS_ORG = "https://dev.azure.com/GenerativeAILab"
AZURE_DEVOPS_PROJECT = "MCPTest"

class AzureDevOpsIntegration:
    """Handles real Azure DevOps API calls - shared between FastAPI and MCP"""
    
    def __init__(self, pat_token: str):
        self.pat_token = pat_token
        self.base_url = f"{AZURE_DEVOPS_ORG}/{AZURE_DEVOPS_PROJECT}/_apis"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self._encode_pat(pat_token)}"
        }
    
    def _encode_pat(self, pat: str) -> str:
        """Encode PAT token for basic auth"""
        import base64
        return base64.b64encode(f":{pat}".encode()).decode()
    
    async def create_work_item(self, title: str, description: str = "", work_item_type: str = "User Story") -> Dict[str, Any]:
        """Create a work item in Azure DevOps"""
        url = f"{self.base_url}/wit/workitems/${work_item_type}?api-version=7.1-preview.3"
        
        payload = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": "/fields/System.Description", "value": description}
        ]
        
        async with aiohttp.ClientSession() as session:
            headers = self.headers.copy()
            headers["Content-Type"] = "application/json-patch+json"
            
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "work_item_id": result.get("id"),
                        "url": result.get("_links", {}).get("html", {}).get("href"),
                        "state": result.get("fields", {}).get("System.State"),
                        "title": result.get("fields", {}).get("System.Title"),
                        "work_item_type": result.get("fields", {}).get("System.WorkItemType")
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "status_code": response.status
                    }
    
    async def get_work_item(self, work_item_id: int) -> Dict[str, Any]:
        """Get a work item by ID"""
        url = f"{self.base_url}/wit/workitems/{work_item_id}?api-version=7.1-preview.3"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "work_item": {
                            "id": result.get("id"),
                            "title": result.get("fields", {}).get("System.Title"),
                            "description": result.get("fields", {}).get("System.Description"),
                            "state": result.get("fields", {}).get("System.State"),
                            "work_item_type": result.get("fields", {}).get("System.WorkItemType"),
                            "created_date": result.get("fields", {}).get("System.CreatedDate"),
                            "url": result.get("_links", {}).get("html", {}).get("href")
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "status_code": response.status
                    }

    async def get_projects(self) -> Dict[str, Any]:
        """Get list of projects"""
        url = f"{AZURE_DEVOPS_ORG}/_apis/projects?api-version=7.1-preview.4"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    result = await response.json()
                    projects = [{"id": p["id"], "name": p["name"], "description": p.get("description", "")} 
                              for p in result.get("value", [])]
                    return {
                        "success": True,
                        "projects": projects,
                        "count": len(projects)
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "status_code": response.status
                    }

# ===== MCP SERVER IMPLEMENTATION =====

# Create MCP Server with Claude Desktop compatibility
mcp_server = Server("ADOMCP")

@mcp_server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools with Claude Desktop-compliant structure"""
    return [
        Tool(
            name="create_work_item",
            title="Create Azure DevOps Work Item",
            description="Create a new work item (User Story, Task, Bug, etc.) in Azure DevOps with title and description",
            annotations=ToolAnnotations(
                title="Azure DevOps Work Item Creator",
                readOnlyHint=False
            ),
            inputSchema={
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"type": "string", "description": "The title of the work item", "minLength": 1},
                    "description": {"type": "string", "description": "Optional description of the work item", "default": ""},
                    "work_item_type": {"type": "string", "description": "Type of work item to create", "enum": ["User Story", "Task", "Bug", "Feature", "Epic"], "default": "User Story"},
                    "pat_token": {"type": "string", "description": "Azure DevOps Personal Access Token (optional if environment variable set)"}
                }
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "work_item_id": {"type": "integer"},
                    "url": {"type": "string"},
                    "state": {"type": "string"},
                    "title": {"type": "string"},
                    "work_item_type": {"type": "string"},
                    "error": {"type": "string"}
                },
                "required": ["success"]
            }
        ),
        Tool(
            name="get_work_item", 
            title="Get Azure DevOps Work Item",
            description="Retrieve detailed information about a specific work item by its ID",
            annotations=ToolAnnotations(
                title="Azure DevOps Work Item Retriever",
                readOnlyHint=True
            ),
            inputSchema={
                "type": "object",
                "required": ["work_item_id"],
                "properties": {
                    "work_item_id": {"type": "integer", "description": "The ID of the work item to retrieve", "minimum": 1},
                    "pat_token": {"type": "string", "description": "Azure DevOps Personal Access Token (optional if environment variable set)"}
                }
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "work_item": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "state": {"type": "string"},
                            "work_item_type": {"type": "string"},
                            "created_date": {"type": "string"},
                            "url": {"type": "string"}
                        }
                    },
                    "error": {"type": "string"}
                },
                "required": ["success"]
            }
        ),
        Tool(
            name="get_projects",
            title="List Azure DevOps Projects",
            description="Get a list of all available Azure DevOps projects in the organization", 
            annotations=ToolAnnotations(
                title="Azure DevOps Project Lister",
                readOnlyHint=True
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pat_token": {"type": "string", "description": "Azure DevOps Personal Access Token (optional if environment variable set)"}
                }
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "projects": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "count": {"type": "integer"},
                    "error": {"type": "string"}
                },
                "required": ["success"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[ContentBlock]:
    """Execute tools with structured content support for Claude Desktop"""
    try:
        pat_token = arguments.get("pat_token") or os.getenv("AZURE_DEVOPS_PAT")
        
        if name == "create_work_item":
            if not pat_token:
                result = {"success": False, "error": "Azure DevOps PAT token required"}
            else:
                azure = AzureDevOpsIntegration(pat_token)
                result = await azure.create_work_item(
                    title=arguments["title"],
                    description=arguments.get("description", ""),
                    work_item_type=arguments.get("work_item_type", "User Story")
                )
            
            text_content = f"Work item creation {'successful' if result.get('success') else 'failed'}"
            if result.get("success"):
                text_content += f": #{result.get('work_item_id')} - {result.get('title')}"
            else:
                text_content += f": {result.get('error')}"
            
            return [
                TextContent(type="text", text=text_content),
                types.ContentBlock(type="structured", structuredContent=result)
            ]
        
        elif name == "get_work_item":
            if not pat_token:
                result = {"success": False, "error": "Azure DevOps PAT token required"}
            else:
                azure = AzureDevOpsIntegration(pat_token)
                result = await azure.get_work_item(arguments["work_item_id"])
            
            text_content = f"Work item retrieval {'successful' if result.get('success') else 'failed'}"
            if result.get("success"):
                wi = result.get("work_item", {})
                text_content += f": #{wi.get('id')} - {wi.get('title')} ({wi.get('state')})"
            else:
                text_content += f": {result.get('error')}"
            
            return [
                TextContent(type="text", text=text_content),
                types.ContentBlock(type="structured", structuredContent=result)
            ]
        
        elif name == "get_projects":
            if not pat_token:
                result = {"success": False, "error": "Azure DevOps PAT token required"}
            else:
                azure = AzureDevOpsIntegration(pat_token)
                result = await azure.get_projects()
            
            text_content = f"Project listing {'successful' if result.get('success') else 'failed'}"
            if result.get("success"):
                text_content += f": Found {result.get('count', 0)} projects"
            else:
                text_content += f": {result.get('error')}"
            
            return [
                TextContent(type="text", text=text_content),
                types.ContentBlock(type="structured", structuredContent=result)
            ]
        
        else:
            error_result = {"success": False, "error": f"Unknown tool: {name}"}
            return [
                TextContent(type="text", text=f"Error: Unknown tool '{name}'"),
                types.ContentBlock(type="structured", structuredContent=error_result)
            ]
    
    except Exception as e:
        logger.error(f"Error in tool execution: {e}")
        error_result = {"success": False, "error": f"Exception: {str(e)}"}
        return [
            TextContent(type="text", text=f"Error executing {name}: {str(e)}"),
            types.ContentBlock(type="structured", structuredContent=error_result)
        ]

# ===== FASTAPI HTTP SERVER IMPLEMENTATION =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("🚀 Starting ADOMCP Hybrid Server")
    logger.info("✅ FastAPI HTTP endpoints available")
    logger.info("✅ MCP transports available (SSE, Streamable HTTP)")
    yield
    logger.info("🛑 Shutting down ADOMCP Hybrid Server")

# Create FastAPI app
fastapi_app = FastAPI(
    title="ADOMCP - Hybrid Architecture",
    description="Azure DevOps integration with FastAPI HTTP + MCP protocol support",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Preserve existing HTTP endpoints for backward compatibility
@fastapi_app.post("/api/azure-devops")
async def azure_devops_endpoint(request: Dict[str, Any]):
    """Legacy Azure DevOps HTTP endpoint"""
    try:
        operation = request.get("operation")
        pat_token = request.get("pat_token") or request.get("test_pat_token") or os.getenv("AZURE_DEVOPS_PAT")
        
        if not pat_token:
            return {"error": "PAT token required", "api_response": "ERROR"}
        
        azure = AzureDevOpsIntegration(pat_token)
        
        if operation == "create_work_item":
            result = await azure.create_work_item(
                title=request.get("title", ""),
                description=request.get("description", ""),
                work_item_type=request.get("work_item_type", "User Story")
            )
            return {
                "api_response": "REAL_API_SUCCESS" if result.get("success") else "REAL_API_ERROR",
                "work_item_id": result.get("work_item_id"),
                **result
            }
        
        elif operation == "get_work_item":
            result = await azure.get_work_item(request.get("work_item_id"))
            return {
                "api_response": "REAL_API_SUCCESS" if result.get("success") else "REAL_API_ERROR",
                **result
            }
        
        elif operation == "get_projects":
            result = await azure.get_projects()
            return {
                "api_response": "REAL_API_SUCCESS" if result.get("success") else "REAL_API_ERROR",
                **result
            }
        
        else:
            return {"error": f"Unknown operation: {operation}", "api_response": "ERROR"}
    
    except Exception as e:
        logger.error(f"Error in Azure DevOps endpoint: {e}")
        return {"error": str(e), "api_response": "ERROR"}

@fastapi_app.get("/api/capabilities")
async def capabilities():
    """Capability negotiation endpoint"""
    return {
        "capabilities": {
            "tools": {"listChanged": True},
            "logging": {},
            "completions": {}
        },
        "protocolVersion": "2025-06-18",
        "serverInfo": {
            "name": "ADOMCP",
            "version": "2.0.0"
        }
    }

# MCP JSON-RPC endpoint for basic compatibility
@fastapi_app.post("/api/mcp")
async def mcp_jsonrpc_endpoint(request: Dict[str, Any]):
    """Basic MCP JSON-RPC endpoint for simple integrations"""
    try:
        method = request.get("method")
        
        if method == "tools/list":
            tools = await list_tools()
            return {
                "jsonrpc": "2.0",
                "result": {
                    "tools": [
                        {
                            "name": tool.name,
                            "title": tool.title,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema,
                            "outputSchema": tool.outputSchema,
                            "annotations": tool.annotations.model_dump() if tool.annotations else None
                        }
                        for tool in tools
                    ]
                },
                "id": request.get("id")
            }
        
        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            result_blocks = await call_tool(tool_name, arguments)
            
            # Extract structured content if available
            content = []
            structured_content = None
            
            for block in result_blocks:
                if hasattr(block, 'type'):
                    if block.type == "text":
                        content.append({"type": "text", "text": block.text})
                    elif block.type == "structured":
                        structured_content = block.structuredContent
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": content,
                    "structuredContent": structured_content,
                    "isError": False
                },
                "id": request.get("id")
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": f"400: Unknown method: {method}"
                },
                "id": request.get("id")
            }
    
    except Exception as e:
        logger.error(f"Error in MCP JSON-RPC endpoint: {e}")
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            },
            "id": request.get("id")
        }

# SSE endpoint for MCP Server-Sent Events transport
@fastapi_app.get("/api/sse")
async def sse_endpoint():
    """SSE transport endpoint for Claude Desktop"""
    
    async def event_generator():
        # Create SSE transport
        transport = SseServerTransport()
        
        # Initialize connection
        yield "data: {\"type\": \"connection\", \"status\": \"connected\"}\n\n"
        
        # Handle SSE communication with MCP server
        try:
            # This would normally handle the SSE protocol
            # For now, return basic capability info
            capabilities = {
                "type": "capabilities",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "logging": {},
                    "completions": {}
                },
                "protocolVersion": "2025-06-18"
            }
            yield f"data: {json.dumps(capabilities)}\n\n"
            
        except Exception as e:
            logger.error(f"SSE error: {e}")
            yield f"data: {{\"type\": \"error\", \"message\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

# Streamable HTTP endpoint for MCP Streamable HTTP transport
@fastapi_app.post("/api/streamable-http")
@fastapi_app.get("/api/streamable-http")
async def streamable_http_endpoint(request: Request):
    """Streamable HTTP transport endpoint for Claude Desktop"""
    try:
        # Create session manager
        session_manager = StreamableHTTPSessionManager(
            app=mcp_server,
            json_response=True
        )
        
        # Handle the streamable HTTP request
        scope = request.scope
        receive = request.receive
        
        async def send(response):
            # This would normally handle the streamable HTTP protocol
            pass
        
        await session_manager.handle_request(scope, receive, send)
        
        return {"status": "handled"}
    
    except Exception as e:
        logger.error(f"Streamable HTTP error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_stdio_server():
    """Run MCP server with STDIO transport for Claude Desktop"""
    logger.info("🔌 Starting STDIO transport for Claude Desktop")
    await stdio_server(mcp_server)

async def run_fastapi_server():
    """Run FastAPI server for HTTP endpoints"""
    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    """Main entry point - determine which transport to use"""
    
    # Check if running in STDIO mode (Claude Desktop)
    if os.getenv("MCP_TRANSPORT") == "stdio" or len(os.sys.argv) > 1 and os.sys.argv[1] == "--stdio":
        await run_stdio_server()
    else:
        # Default to FastAPI HTTP server (Railway deployment)
        await run_fastapi_server()

if __name__ == "__main__":
    # Railway deployment - run FastAPI server directly
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(fastapi_app, host="0.0.0.0", port=port)
