"""
Health Check endpoint for Azure DevOps Multi-Platform MCP
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
from datetime import datetime

app = FastAPI()

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "Azure DevOps Multi-Platform MCP",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("VERCEL_ENV", "development"),
        "mcp_capabilities": [
            "work_item_management",
            "attachment_support", 
            "cross_platform_integration",
            "github_integration",
            "hierarchical_structure",
            "secure_api_key_storage"
        ]
    })

@app.get("/api/health")
async def api_health():
    """API Health check"""
    return await health_check()

# For Vercel deployment
from mangum import Mangum

# Create the handler for Vercel
handler = Mangum(app)
