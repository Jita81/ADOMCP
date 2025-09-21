#!/usr/bin/env python3
"""
ADOMCP - Railway Deployment (Minimal Version)
Focuses on reliable HTTP deployment, Claude Desktop integration via mcp_server_enhanced.py
"""

import os
import logging
import uvicorn
from typing import Any, Dict, List, Optional
import aiohttp
import json
from contextlib import asynccontextmanager

# FastAPI imports - core dependencies only
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure DevOps configuration
AZURE_DEVOPS_ORG = "https://dev.azure.com/GenerativeAILab"
AZURE_DEVOPS_PROJECT = "MCPTest"

class AzureDevOpsIntegration:
    """Handles real Azure DevOps API calls"""
    
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("🚀 Starting ADOMCP Minimal Railway Deployment")
    logger.info("✅ FastAPI HTTP endpoints available")
    logger.info("🎯 Claude Desktop: Use mcp_server_enhanced.py locally")
    yield
    logger.info("🛑 Shutting down ADOMCP")

# Create FastAPI app
app = FastAPI(
    title="ADOMCP - Hybrid Architecture",
    description="Azure DevOps integration with HTTP endpoints + local MCP server support",
    version="2.0.0-railway",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint with feature detection
@app.get("/")
async def health_check():
    """Enhanced health check endpoint"""
    return {
        "status": "healthy",
        "service": "ADOMCP Hybrid Architecture",
        "version": "2.0.0-railway", 
        "deployment": "railway-minimal",
        "features": {
            "http_endpoints": True,
            "mcp_protocol": False,  # Not in Railway deployment
            "azure_devops": True,
            "claude_desktop_ready": True,  # Via local mcp_server_enhanced.py
            "claude_desktop_instructions": "Use mcp_server_enhanced.py locally with STDIO transport"
        },
        "endpoints": {
            "azure_devops": "/api/azure-devops",
            "capabilities": "/api/capabilities", 
            "mcp_basic": "/api/mcp",
            "test": "/api/test"
        }
    }

# Azure DevOps endpoint - preserved from original
@app.post("/api/azure-devops")
async def azure_devops_endpoint(request: Dict[str, Any]):
    """Azure DevOps HTTP endpoint"""
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

@app.get("/api/capabilities")
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
            "version": "2.0.0-railway"
        },
        "deployment": {
            "type": "railway-minimal",
            "mcp_sdk": False,
            "claude_desktop": "Use local mcp_server_enhanced.py"
        }
    }

# Basic MCP JSON-RPC endpoint (minimal implementation)
@app.post("/api/mcp")
async def mcp_jsonrpc_endpoint(request: Dict[str, Any]):
    """Basic MCP JSON-RPC endpoint"""
    try:
        method = request.get("method")
        
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "tools": [
                        {
                            "name": "create_work_item",
                            "description": "Create Azure DevOps work item",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "work_item_type": {"type": "string"},
                                    "description": {"type": "string"}
                                }
                            }
                        },
                        {
                            "name": "get_projects",
                            "description": "Get Azure DevOps projects",
                            "inputSchema": {"type": "object", "properties": {}}
                        }
                    ]
                },
                "id": request.get("id")
            }
        
        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": f"Tool {tool_name} executed with arguments: {arguments}. Use local mcp_server_enhanced.py for full Claude Desktop integration."}]
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

# Test endpoint
@app.get("/api/test")
async def test_endpoint():
    """Test endpoint"""
    return {
        "status": "ok", 
        "message": "ADOMCP Railway deployment is working",
        "version": "2.0.0-railway",
        "claude_desktop": "Use mcp_server_enhanced.py locally for full MCP integration"
    }

if __name__ == "__main__":
    # Railway deployment
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
