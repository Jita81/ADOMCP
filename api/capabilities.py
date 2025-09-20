"""
API capabilities endpoint for Vercel
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
from mangum import Mangum

app = FastAPI()

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
            },
            {
                "name": "get_work_item_attachments",
                "description": "Retrieve all attachments for a work item",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "work_item_id": {"type": "integer"},
                        "project": {"type": "string"}
                    },
                    "required": ["work_item_id", "project"]
                }
            },
            {
                "name": "create_epic_feature_story",
                "description": "Create a hierarchical structure of Epic, Features, and User Stories",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "epic_title": {"type": "string"},
                        "epic_description": {"type": "string"},
                        "features": {"type": "array"}
                    },
                    "required": ["epic_title", "features"]
                }
            }
        ],
        "resources": ["work_items", "attachments", "repositories"],
        "version": "2.2.0",
        "timestamp": datetime.now().isoformat(),
        "mcp_protocol": "JSON-RPC 2.0"
    })

@app.get("/")
async def root():
    return await get_capabilities()

# Vercel handler
handler = Mangum(app)
