"""
FastAPI entrypoint for Vercel deployment
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI(
    title="Azure DevOps Multi-Platform MCP",
    description="Model Context Protocol server for Azure DevOps, GitHub, and GitLab integration",
    version="2.2.0"
)

@app.get("/")
async def root():
    return JSONResponse({
        "status": "healthy",
        "service": "Azure DevOps Multi-Platform MCP",
        "version": "2.2.0",
        "timestamp": datetime.now().isoformat(),
        "message": "Vercel deployment successful!",
        "endpoints": {
            "health": "/health",
            "test": "/api/test",
            "capabilities": "/api/capabilities",
            "mcp": "/api/mcp"
        },
        "api_info": {
            "note": "Each /api/* endpoint is a separate Vercel function",
            "protocol": "REST + JSON-RPC 2.0 for MCP"
        },
        "docs": "/docs"
    })

@app.get("/health")
async def health():
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Azure DevOps Multi-Platform MCP"
    })

@app.get("/test")
async def test_redirect():
    """Redirect to API test endpoint"""
    return JSONResponse({
        "message": "Use /api/test for the actual API test endpoint",
        "redirect": "/api/test",
        "timestamp": datetime.now().isoformat()
    })

@app.get("/capabilities") 
async def capabilities_redirect():
    """Redirect to API capabilities endpoint"""
    return JSONResponse({
        "message": "Use /api/capabilities for the actual capabilities endpoint",
        "redirect": "/api/capabilities", 
        "timestamp": datetime.now().isoformat()
    })

@app.get("/mcp")
async def mcp_redirect():
    """Redirect to API MCP endpoint"""
    return JSONResponse({
        "message": "Use /api/mcp for the actual MCP endpoint",
        "redirect": "/api/mcp",
        "timestamp": datetime.now().isoformat()
    })

# This is the FastAPI app that Vercel will use
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
