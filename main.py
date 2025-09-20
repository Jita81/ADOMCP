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

# Dynamic API endpoint handler
@app.api_route("/api/{endpoint:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def api_handler(endpoint: str, request: Request):
    """Dynamic handler for all API endpoints"""
    try:
        # Map endpoint to module name
        module_mapping = {
            "auth": "auth",
            "oauth": "oauth", 
            "secure-keys": "secure_keys",
            "secure_keys": "secure_keys",
            "secure-mcp": "secure_mcp",
            "secure_mcp": "secure_mcp",
            "oauth-mcp": "oauth_mcp",
            "oauth_mcp": "oauth_mcp",
            "azure-devops": "azure-devops",
            "github": "github",
            "capabilities": "capabilities",
            "mcp": "mcp",
            "test": "test"
        }
        
        module_name = module_mapping.get(endpoint, endpoint)
        handler_class = load_api_handler(module_name)
        
        if not handler_class:
            raise HTTPException(status_code=404, detail=f"Endpoint {endpoint} not found")
        
        # Create handler instance and process request
        handler = handler_class()
        
        # Convert FastAPI request to format expected by BaseHTTPRequestHandler
        handler.path = f"/api/{endpoint}"
        handler.command = request.method
        
        # Handle request body
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            handler.rfile = body
        
        # Process request based on method
        if request.method == "GET":
            if hasattr(handler, 'do_GET'):
                handler.do_GET()
        elif request.method == "POST":
            if hasattr(handler, 'do_POST'):
                handler.do_POST()
        elif request.method == "PUT":
            if hasattr(handler, 'do_PUT'):
                handler.do_PUT()
        elif request.method == "DELETE":
            if hasattr(handler, 'do_DELETE'):
                handler.do_DELETE()
        else:
            raise HTTPException(status_code=405, detail="Method not allowed")
            
        # Return response (this is a simplified implementation)
        # In practice, you'd need to capture the handler's response
        return {"message": "Request processed", "endpoint": endpoint}
        
    except Exception as e:
        print(f"Error in API handler for {endpoint}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)