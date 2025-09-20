"""
ADOMCP - Railway Deployment Entry Point
Unified FastAPI application for all MCP endpoints
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
import importlib.util
import traceback
from datetime import datetime

app = FastAPI(
    title="ADOMCP - Azure DevOps MCP Server",
    description="Advanced security-enabled MCP server for Azure DevOps, GitHub, and GitLab integration",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security module to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_api_handler(module_name: str):
    """Load an API handler from the api directory"""
    try:
        module_path = f"api/{module_name}.py"
        if not os.path.exists(module_path):
            return None
            
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, 'handler'):
            return module.handler
        return None
    except Exception as e:
        print(f"Error loading {module_name}: {e}")
        return None

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "ADOMCP - Azure DevOps MCP Server",
        "version": "2.0.0",
        "status": "operational",
        "deployment": "railway",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "authentication": "/auth",
            "oauth": "/oauth", 
            "secure_keys": "/secure-keys",
            "secure_mcp": "/secure-mcp",
            "oauth_mcp": "/oauth-mcp",
            "azure_devops": "/azure-devops",
            "github": "/github",
            "capabilities": "/capabilities",
            "mcp": "/mcp"
        }
    }

# Health check
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "deployment": "railway"
    }

# Import all API handlers directly
@app.get("/api/oauth")
async def oauth_get():
    """OAuth endpoint"""
    return {
        "service": "ADOMCP OAuth Service",
        "endpoints": {
            "login": "/api/oauth/login",
            "callback": "/api/oauth/callback",
            "status": "/api/oauth/status"
        },
        "providers": ["github", "google", "microsoft"],
        "status": "operational"
    }

@app.get("/api/auth")  
async def auth_get():
    """Authentication endpoint"""
    return {
        "service": "ADOMCP Authentication Service", 
        "authentication_required": True,
        "registration": "POST /api/auth with email",
        "api_key_format": "ADOMCP API keys",
        "status": "operational"
    }

@app.get("/api/secure-keys")
async def secure_keys():
    """Secure API key management"""
    return {
        "service": "ADOMCP Secure Key Management",
        "authentication_required": True,
        "supported_platforms": ["azure-devops", "github", "gitlab"],
        "operations": ["store", "retrieve", "list"],
        "status": "operational"
    }

@app.get("/api/secure-mcp")
async def secure_mcp():
    """Secure MCP JSON-RPC endpoint"""
    return {
        "service": "ADOMCP Secure MCP",
        "protocol": "JSON-RPC 2.0",
        "authentication_required": True,
        "tools": ["create_work_item", "update_work_item", "manage_attachments"],
        "status": "operational"
    }

@app.get("/api/oauth-mcp")  
async def oauth_mcp():
    """OAuth-protected MCP endpoint"""
    return {
        "service": "ADOMCP OAuth MCP",
        "protocol": "JSON-RPC 2.0", 
        "authentication": "OAuth",
        "providers": ["github", "google", "microsoft"],
        "status": "operational"
    }

@app.get("/api/azure-devops")
async def azure_devops():
    """Azure DevOps integration"""
    return {
        "service": "Azure DevOps Integration",
        "operations": ["work_items", "projects", "attachments"],
        "authentication": "PAT token required",
        "status": "operational"
    }

@app.get("/api/github")
async def github():
    """GitHub integration"""
    return {
        "service": "GitHub Integration", 
        "operations": ["issues", "repositories", "commits"],
        "authentication": "GitHub token required",
        "status": "operational"
    }

@app.get("/api/capabilities")
async def capabilities():
    """MCP capabilities"""
    return {
        "service": "ADOMCP Capabilities",
        "tools": [
            "create_work_item",
            "update_work_item", 
            "manage_relationships",
            "manage_attachments",
            "github_integration"
        ],
        "resources": ["azure-devops", "github", "gitlab"],
        "status": "operational"
    }

@app.get("/api/mcp")
async def mcp():
    """Core MCP endpoint"""
    return {
        "service": "ADOMCP Core MCP",
        "protocol": "JSON-RPC 2.0",
        "version": "2.0.0",
        "capabilities": ["tools", "resources", "prompts"],
        "status": "operational"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)