#!/usr/bin/env python3
"""
ADOMCP - Enhanced MCP Server Implementation with Full Claude Desktop Compatibility
Includes tool titles, output schemas, and structured content support
"""

import asyncio
import os
import logging
from typing import Any, Dict, List, Optional, Union
import aiohttp
import json
from urllib.parse import quote

# MCP SDK imports - Using lowlevel Server for maximum control
from mcp.server.lowlevel import Server
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

# Create MCP Server with Claude Desktop compatibility
app = Server("ADOMCP")

@app.list_tools()
async def list_tools() -> List[Tool]:
    """
    List all available tools with Claude Desktop-compliant structure.
    Each tool includes required title, descriptions, and output schemas.
    """
    return [
        Tool(
            name="create_work_item",
            title="Create Azure DevOps Work Item",  # ✅ Required for Claude Desktop
            description="Create a new work item (User Story, Task, Bug, etc.) in Azure DevOps with title and description",
            annotations=ToolAnnotations(
                title="Azure DevOps Work Item Creator",
                readOnlyHint=False
            ),
            inputSchema={
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the work item",
                        "minLength": 1
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description of the work item",
                        "default": ""
                    },
                    "work_item_type": {
                        "type": "string", 
                        "description": "Type of work item to create",
                        "enum": ["User Story", "Task", "Bug", "Feature", "Epic"],
                        "default": "User Story"
                    },
                    "pat_token": {
                        "type": "string",
                        "description": "Azure DevOps Personal Access Token (optional if environment variable set)"
                    }
                }
            },
            # ✅ Output schema required for Claude Desktop structured responses
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
            title="Get Azure DevOps Work Item",  # ✅ Required for Claude Desktop
            description="Retrieve detailed information about a specific work item by its ID",
            annotations=ToolAnnotations(
                title="Azure DevOps Work Item Retriever",
                readOnlyHint=True  # This tool doesn't modify data
            ),
            inputSchema={
                "type": "object",
                "required": ["work_item_id"],
                "properties": {
                    "work_item_id": {
                        "type": "integer",
                        "description": "The ID of the work item to retrieve",
                        "minimum": 1
                    },
                    "pat_token": {
                        "type": "string",
                        "description": "Azure DevOps Personal Access Token (optional if environment variable set)"
                    }
                }
            },
            # ✅ Output schema for structured work item data
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
            title="List Azure DevOps Projects",  # ✅ Required for Claude Desktop
            description="Get a list of all available Azure DevOps projects in the organization",
            annotations=ToolAnnotations(
                title="Azure DevOps Project Lister",
                readOnlyHint=True  # This tool doesn't modify data
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pat_token": {
                        "type": "string",
                        "description": "Azure DevOps Personal Access Token (optional if environment variable set)"
                    }
                }
            },
            # ✅ Output schema for project list
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
        ),
        Tool(
            name="update_work_item",
            title="Update Azure DevOps Work Item",  # ✅ Required for Claude Desktop
            description="Update an existing work item's title, description, or state",
            annotations=ToolAnnotations(
                title="Azure DevOps Work Item Updater",
                readOnlyHint=False
            ),
            inputSchema={
                "type": "object",
                "required": ["work_item_id"],
                "properties": {
                    "work_item_id": {
                        "type": "integer",
                        "description": "The ID of the work item to update",
                        "minimum": 1
                    },
                    "title": {
                        "type": "string",
                        "description": "New title for the work item"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description for the work item"
                    },
                    "state": {
                        "type": "string",
                        "description": "New state for the work item",
                        "enum": ["New", "Active", "Resolved", "Test", "Closed"]
                    },
                    "pat_token": {
                        "type": "string",
                        "description": "Azure DevOps Personal Access Token (optional if environment variable set)"
                    }
                }
            },
            # ✅ Output schema for update results
            outputSchema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "work_item_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "state": {"type": "string"},
                    "url": {"type": "string"},
                    "error": {"type": "string"}
                },
                "required": ["success"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[ContentBlock]:
    """
    Execute tools with structured content support for Claude Desktop.
    Returns both text content and structured data.
    """
    try:
        # Get PAT token from arguments or environment
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
            
            # Return both text and structured content for Claude Desktop
            text_content = f"Work item creation {'successful' if result.get('success') else 'failed'}"
            if result.get("success"):
                text_content += f": #{result.get('work_item_id')} - {result.get('title')}"
            else:
                text_content += f": {result.get('error')}"
            
            return [
                TextContent(type="text", text=text_content),
                # ✅ Structured content for Claude Desktop - using dict directly
                {
                    "type": "structured",
                    "structuredContent": result
                }
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
                {
                    "type": "structured", 
                    "structuredContent": result
                }
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
                {
                    "type": "structured",
                    "structuredContent": result
                }
            ]
        
        elif name == "update_work_item":
            if not pat_token:
                result = {"success": False, "error": "Azure DevOps PAT token required"}
            else:
                # Build update operations
                updates = {}
                if "title" in arguments:
                    updates["title"] = arguments["title"]
                if "description" in arguments:
                    updates["description"] = arguments["description"]
                if "state" in arguments:
                    updates["state"] = arguments["state"]
                
                if not updates:
                    result = {
                        "success": False,
                        "error": "At least one field (title, description, state) must be provided for update"
                    }
                else:
                    azure = AzureDevOpsIntegration(pat_token)
                    url = f"{azure.base_url}/wit/workitems/{arguments['work_item_id']}?api-version=7.1-preview.3"
                    
                    # Build patch operations
                    patch_ops = []
                    if "title" in updates:
                        patch_ops.append({"op": "replace", "path": "/fields/System.Title", "value": updates["title"]})
                    if "description" in updates:
                        patch_ops.append({"op": "replace", "path": "/fields/System.Description", "value": updates["description"]})
                    if "state" in updates:
                        patch_ops.append({"op": "replace", "path": "/fields/System.State", "value": updates["state"]})
                    
                    async with aiohttp.ClientSession() as session:
                        headers = azure.headers.copy()
                        headers["Content-Type"] = "application/json-patch+json"
                        
                        async with session.patch(url, json=patch_ops, headers=headers) as response:
                            if response.status == 200:
                                update_result = await response.json()
                                result = {
                                    "success": True,
                                    "work_item_id": update_result.get("id"),
                                    "title": update_result.get("fields", {}).get("System.Title"),
                                    "state": update_result.get("fields", {}).get("System.State"),
                                    "url": update_result.get("_links", {}).get("html", {}).get("href")
                                }
                            else:
                                error_text = await response.text()
                                result = {
                                    "success": False,
                                    "error": f"HTTP {response.status}: {error_text}",
                                    "status_code": response.status
                                }
            
            text_content = f"Work item update {'successful' if result.get('success') else 'failed'}"
            if result.get("success"):
                text_content += f": #{result.get('work_item_id')} - {result.get('title')}"
            else:
                text_content += f": {result.get('error')}"
            
            return [
                TextContent(type="text", text=text_content),
                {
                    "type": "structured",
                    "structuredContent": result
                }
            ]
        
        else:
            # Unknown tool
            error_result = {"success": False, "error": f"Unknown tool: {name}"}
            return [
                TextContent(type="text", text=f"Error: Unknown tool '{name}'"),
                types.ContentBlock(
                    type="structured",
                    structuredContent=error_result
                )
            ]
    
    except Exception as e:
        logger.error(f"Error in tool execution: {e}")
        error_result = {"success": False, "error": f"Exception: {str(e)}"}
        return [
            TextContent(type="text", text=f"Error executing {name}: {str(e)}"),
            {
                "type": "structured", 
                "structuredContent": error_result
            }
        ]

async def main():
    """Run the MCP server with STDIO transport for Claude Desktop"""
    # Use STDIO transport for Claude Desktop compatibility
    from mcp.server.stdio import stdio_server
    
    logger.info("🚀 Starting ADOMCP Enhanced MCP Server for Claude Desktop")
    logger.info("✅ Features: Tool titles, output schemas, structured content")
    logger.info("🔌 Transport: STDIO (Claude Desktop compatible)")
    
    await stdio_server(app)

if __name__ == "__main__":
    asyncio.run(main())
