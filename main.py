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
            "capabilities": "/api/capabilities", 
            "test": "/api/test"
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

@app.get("/api/test")
async def api_test():
    return JSONResponse({
        "test": "success",
        "message": "External API access verified",
        "timestamp": datetime.now().isoformat(),
        "deployment": "vercel"
    })

@app.get("/api/capabilities")
async def get_capabilities():
    return JSONResponse({
        "tools": [
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
        ],
        "resources": ["work_items", "attachments", "repositories"],
        "version": "2.2.0"
    })

# This is the FastAPI app that Vercel will use
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
