#!/usr/bin/env python3
"""
ADOMCP - Azure DevOps MCP Server (Official SDK Compliant)

A fully compliant Model Context Protocol server for Azure DevOps and GitHub integration,
built using the official MCP Python SDK patterns and supporting StreamableHTTP transport
for Claude Desktop compatibility.
"""

import os
import logging
import contextlib
from collections.abc import AsyncIterator
from typing import Any
import json
import base64

import anyio
import click
import aiohttp
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Azure DevOps and GitHub API integration functions
class AzureDevOpsAPI:
    """Azure DevOps API client for work item operations"""
    
    def __init__(self, pat_token: str, organization: str = "GenerativeAILab", project: str = "MCPTest"):
        self.pat_token = pat_token
        self.organization = organization
        self.project = project
        self.base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
        
    async def create_work_item(self, title: str, work_item_type: str = "User Story", 
                             description: str = "", **kwargs) -> dict[str, Any]:
        """Create a new work item in Azure DevOps"""
        try:
            auth_header = base64.b64encode(f":{self.pat_token}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/json-patch+json"
            }
            
            # Build the work item fields
            fields = [
                {"op": "add", "path": "/fields/System.Title", "value": title},
                {"op": "add", "path": "/fields/System.WorkItemType", "value": work_item_type}
            ]
            
            if description:
                fields.append({"op": "add", "path": "/fields/System.Description", "value": description})
            
            # Add optional fields
            if kwargs.get("area_path"):
                fields.append({"op": "add", "path": "/fields/System.AreaPath", "value": kwargs["area_path"]})
            if kwargs.get("iteration_path"):
                fields.append({"op": "add", "path": "/fields/System.IterationPath", "value": kwargs["iteration_path"]})
            if kwargs.get("assigned_to"):
                fields.append({"op": "add", "path": "/fields/System.AssignedTo", "value": kwargs["assigned_to"]})
            if kwargs.get("tags"):
                fields.append({"op": "add", "path": "/fields/System.Tags", "value": kwargs["tags"]})
            
            url = f"{self.base_url}/wit/workitems/${work_item_type}?api-version=7.1-preview.3"
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=headers, json=fields) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "work_item_id": result["id"],
                            "work_item_type": result["fields"]["System.WorkItemType"],
                            "work_item_url": result["_links"]["html"]["href"],
                            "message": f"Work item '{title}' created successfully"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "message": f"Failed to create work item: {response.status} - {error_text}"
                        }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating work item: {str(e)}"
            }

    async def update_work_item(self, work_item_id: int, updates: dict[str, Any]) -> dict[str, Any]:
        """Update an existing work item in Azure DevOps"""
        try:
            auth_header = base64.b64encode(f":{self.pat_token}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/json-patch+json"
            }
            
            # Convert updates to JSON patch format
            fields = []
            for field_path, value in updates.items():
                if not field_path.startswith("/fields/"):
                    field_path = f"/fields/{field_path}"
                fields.append({"op": "replace", "path": field_path, "value": value})
            
            url = f"{self.base_url}/wit/workitems/{work_item_id}?api-version=7.1-preview.3"
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=headers, json=fields) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "work_item_id": result["id"],
                            "updates_applied": len(fields),
                            "work_item_url": result["_links"]["html"]["href"],
                            "message": f"Work item {work_item_id} updated successfully"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "message": f"Failed to update work item: {response.status} - {error_text}"
                        }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error updating work item: {str(e)}"
            }

class GitHubAPI:
    """GitHub API client for repository operations"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        
    async def create_issue(self, repository: str, title: str, description: str = "", **kwargs) -> dict[str, Any]:
        """Create a new issue in GitHub repository"""
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            issue_data = {
                "title": title,
                "body": description
            }
            
            if kwargs.get("labels"):
                issue_data["labels"] = kwargs["labels"]
            if kwargs.get("assignees"):
                issue_data["assignees"] = kwargs["assignees"]
            
            url = f"{self.base_url}/repos/{repository}/issues"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=issue_data) as response:
                    if response.status == 201:
                        result = await response.json()
                        return {
                            "success": True,
                            "issue_id": result["number"],
                            "issue_url": result["html_url"],
                            "message": f"Issue '{title}' created successfully in {repository}"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "message": f"Failed to create issue: {response.status} - {error_text}"
                        }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating issue: {str(e)}"
            }

    async def list_repositories(self, owner: str = None) -> dict[str, Any]:
        """List repositories for the authenticated user or specified owner"""
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            if owner:
                url = f"{self.base_url}/users/{owner}/repos"
            else:
                url = f"{self.base_url}/user/repos"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        repos = await response.json()
                        repo_list = [{"name": repo["name"], "url": repo["html_url"]} for repo in repos[:10]]
                        return {
                            "success": True,
                            "repositories": repo_list,
                            "message": f"Found {len(repo_list)} repositories"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "message": f"Failed to list repositories: {response.status} - {error_text}"
                        }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error listing repositories: {str(e)}"
            }

@click.command()
@click.option("--port", default=3000, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO", 
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses instead of SSE streams",
)
def main(port: int, log_level: str, json_response: bool) -> int:
    """Start the ADOMCP server with official MCP SDK compliance"""
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Create the MCP server using official SDK
    app = Server("ADOMCP")
    
    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        """Handle tool calls using official MCP SDK patterns"""
        
        # Get environment variables for API tokens
        azure_pat = os.getenv("AZURE_DEVOPS_PAT")
        github_token = os.getenv("GITHUB_TOKEN")
        
        try:
            if name == "create_work_item":
                if not azure_pat:
                    return [types.TextContent(
                        type="text",
                        text="❌ Error: AZURE_DEVOPS_PAT environment variable not set"
                    )]
                
                azure_api = AzureDevOpsAPI(azure_pat)
                result = await azure_api.create_work_item(
                    title=arguments.get("title", "MCP Created Work Item"),
                    work_item_type=arguments.get("work_item_type", "User Story"),
                    description=arguments.get("description", "Created via MCP tool call"),
                    area_path=arguments.get("area_path"),
                    iteration_path=arguments.get("iteration_path"),
                    assigned_to=arguments.get("assigned_to"),
                    tags=arguments.get("tags")
                )
                
                if result["success"]:
                    response_text = f"✅ Work item '{arguments.get('title')}' created successfully!\n"
                    response_text += f"• Work Item ID: {result['work_item_id']}\n"
                    response_text += f"• Type: {result['work_item_type']}\n"
                    response_text += f"• URL: {result['work_item_url']}"
                else:
                    response_text = f"❌ Failed to create work item: {result['message']}"
                
                return [types.TextContent(type="text", text=response_text)]
                
            elif name == "update_work_item":
                if not azure_pat:
                    return [types.TextContent(
                        type="text",
                        text="❌ Error: AZURE_DEVOPS_PAT environment variable not set"
                    )]
                
                work_item_id = arguments.get("work_item_id")
                if not work_item_id:
                    return [types.TextContent(
                        type="text",
                        text="❌ Error: work_item_id is required for update_work_item"
                    )]
                
                azure_api = AzureDevOpsAPI(azure_pat)
                result = await azure_api.update_work_item(
                    work_item_id=work_item_id,
                    updates=arguments.get("updates", {})
                )
                
                if result["success"]:
                    response_text = f"✅ Work item {work_item_id} updated successfully!\n"
                    response_text += f"• Fields updated: {result['updates_applied']}\n"
                    response_text += f"• URL: {result['work_item_url']}"
                else:
                    response_text = f"❌ Failed to update work item: {result['message']}"
                
                return [types.TextContent(type="text", text=response_text)]
                
            elif name == "github_integration":
                if not github_token:
                    return [types.TextContent(
                        type="text",
                        text="❌ Error: GITHUB_TOKEN environment variable not set"
                    )]
                
                github_api = GitHubAPI(github_token)
                action = arguments.get("action", "create_issue")
                
                if action == "create_issue":
                    result = await github_api.create_issue(
                        repository=arguments.get("repository", "Jita81/ADOMCP"),
                        title=arguments.get("title", "MCP Created Issue"),
                        description=arguments.get("description", "Created via MCP tool call"),
                        labels=arguments.get("labels", []),
                        assignees=arguments.get("assignees", [])
                    )
                    
                    if result["success"]:
                        response_text = f"✅ GitHub issue created successfully!\n"
                        response_text += f"• Issue ID: {result['issue_id']}\n"
                        response_text += f"• URL: {result['issue_url']}"
                    else:
                        response_text = f"❌ Failed to create issue: {result['message']}"
                        
                elif action == "list_repositories":
                    result = await github_api.list_repositories()
                    
                    if result["success"]:
                        response_text = f"✅ Found {len(result['repositories'])} repositories:\n"
                        for repo in result["repositories"]:
                            response_text += f"• {repo['name']}: {repo['url']}\n"
                    else:
                        response_text = f"❌ Failed to list repositories: {result['message']}"
                        
                else:
                    response_text = f"❌ Unknown GitHub action: {action}"
                
                return [types.TextContent(type="text", text=response_text)]
                
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Unknown tool: {name}"
                )]
                
        except Exception as e:
            logger.error(f"Tool execution error: {str(e)}")
            return [types.TextContent(
                type="text",
                text=f"❌ Tool execution failed: {str(e)}"
            )]

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List available tools using official MCP SDK patterns"""
        return [
            types.Tool(
                name="create_work_item",
                description="Create a new work item in Azure DevOps",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the work item"
                        },
                        "work_item_type": {
                            "type": "string",
                            "description": "Type of work item (User Story, Bug, Task, etc.)",
                            "default": "User Story"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the work item"
                        },
                        "area_path": {
                            "type": "string",
                            "description": "Area path for the work item"
                        },
                        "iteration_path": {
                            "type": "string",
                            "description": "Iteration path for the work item"
                        },
                        "assigned_to": {
                            "type": "string",
                            "description": "Email of user to assign the work item to"
                        },
                        "tags": {
                            "type": "string",
                            "description": "Tags for the work item (semicolon separated)"
                        }
                    },
                    "required": ["title"]
                }
            ),
            types.Tool(
                name="update_work_item",
                description="Update an existing work item in Azure DevOps",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "integer",
                            "description": "ID of the work item to update"
                        },
                        "updates": {
                            "type": "object",
                            "description": "Fields to update (e.g., {'System.Title': 'New Title', 'System.State': 'Active'})"
                        }
                    },
                    "required": ["work_item_id", "updates"]
                }
            ),
            types.Tool(
                name="github_integration",
                description="Integrate with GitHub repositories and issues",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "Action to perform (create_issue, list_repositories)",
                            "enum": ["create_issue", "list_repositories"]
                        },
                        "repository": {
                            "type": "string",
                            "description": "Repository in format 'owner/repo'",
                            "default": "Jita81/ADOMCP"
                        },
                        "title": {
                            "type": "string",
                            "description": "Title for new issue (when action=create_issue)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description for new issue (when action=create_issue)"
                        },
                        "labels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Labels for new issue (when action=create_issue)"
                        },
                        "assignees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Assignees for new issue (when action=create_issue)"
                        }
                    },
                    "required": ["action"]
                }
            )
        ]

    # Create the StreamableHTTP session manager for Claude Desktop compatibility
    session_manager = StreamableHTTPSessionManager(
        app=app,
        json_response=json_response,
    )

    # ASGI handler for streamable HTTP connections
    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for managing session manager lifecycle."""
        async with session_manager.run():
            logger.info("ADOMCP Server started with StreamableHTTP session manager!")
            logger.info(f"Server running on port {port}")
            logger.info("Ready for Claude Desktop connections!")
            try:
                yield
            finally:
                logger.info("ADOMCP Server shutting down...")

    # Create the Starlette ASGI application
    starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    # Add CORS middleware for browser compatibility
    starlette_app = CORSMiddleware(
        starlette_app,
        allow_origins=["*"],  # Allow all origins - adjust for production
        allow_methods=["GET", "POST", "DELETE"],  # MCP streamable HTTP methods
        expose_headers=["Mcp-Session-Id"],
    )

    import uvicorn
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main()
