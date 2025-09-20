#!/usr/bin/env python3
"""
ADOMCP - Hybrid MCP Server (Railway Compatible + MCP SDK Compliant)

A hybrid approach that provides MCP SDK compliance while maintaining Railway deployment compatibility.
Uses FastAPI for Railway stability with MCP SDK patterns for tool definitions.
"""

import os
import sys
import logging
from typing import Any, Dict, List, Optional
import json
import base64
import asyncio

from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import aiohttp
import uvicorn

# Add security modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from security.authentication import AuthenticationManager, AuthToken
    from security import (SecurityValidator, check_rate_limit, get_security_headers, 
                         encrypt_api_key_advanced, decrypt_api_key_advanced)
    SECURITY_AVAILABLE = True
except ImportError:
    logger.warning("Security modules not available - using environment variables only")
    SECURITY_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize authentication if available
auth_manager = None
security_bearer = HTTPBearer(auto_error=False)

if SECURITY_AVAILABLE:
    auth_manager = AuthenticationManager()
    logger.info("🔐 Authentication system initialized")
else:
    logger.info("🔓 Using environment variables only (no authentication system)")

# Azure DevOps and GitHub API integration (same as compliant version)
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

# FastAPI application for Railway compatibility
app = FastAPI(title="ADOMCP - Hybrid MCP Server", version="1.0.0")

# CORS middleware for Claude Desktop compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"]
)

# Authentication helper functions
async def get_api_tokens_from_auth(user_api_key: str) -> Dict[str, str]:
    """Get platform API tokens from authenticated user storage"""
    if not SECURITY_AVAILABLE or not auth_manager:
        logger.debug("Security system not available, skipping user authentication")
        return {}
    
    try:
        # Authenticate the user API key and get stored platform tokens
        auth_result = auth_manager.authenticate_api_key(user_api_key)
        if not auth_result or not auth_result.get("valid"):
            logger.debug("User API key authentication failed")
            return {}
        
        user_id = auth_result.get("user_id")
        if not user_id:
            logger.debug("No user ID from authentication result")
            return {}
        
        # Get encrypted platform API keys from storage
        # Note: This is a simplified version - in production you'd use a database
        stored_keys = {}
        azure_key = os.getenv(f"USER_{user_id}_AZURE_PAT")
        github_key = os.getenv(f"USER_{user_id}_GITHUB_TOKEN")
        
        if azure_key:
            try:
                stored_keys["azure_pat"] = decrypt_api_key_advanced(azure_key) if SECURITY_AVAILABLE else azure_key
            except Exception as decrypt_error:
                logger.warning(f"Failed to decrypt Azure PAT for user {user_id}: {decrypt_error}")
        
        if github_key:
            try:
                stored_keys["github_token"] = decrypt_api_key_advanced(github_key) if SECURITY_AVAILABLE else github_key
            except Exception as decrypt_error:
                logger.warning(f"Failed to decrypt GitHub token for user {user_id}: {decrypt_error}")
            
        logger.debug(f"Retrieved {len(stored_keys)} API keys for user {user_id}")
        return stored_keys
        
    except Exception as e:
        logger.warning(f"Authentication system error (falling back to env vars): {str(e)}")
        return {}

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> Optional[str]:
    """Get current authenticated user from API key"""
    if not credentials or not SECURITY_AVAILABLE or not auth_manager:
        return None
    
    try:
        auth_result = auth_manager.authenticate_api_key(credentials.credentials)
        if auth_result.get("valid"):
            return auth_result.get("user_id")
    except Exception:
        pass
    
    return None

# MCP Tools Definitions (using MCP SDK patterns but implemented in FastAPI)
MCP_TOOLS = [
    {
        "name": "create_work_item",
        "description": "Create a new work item in Azure DevOps",
        "inputSchema": {
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
    },
    {
        "name": "update_work_item",
        "description": "Update an existing work item in Azure DevOps",
        "inputSchema": {
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
    },
    {
        "name": "github_integration",
        "description": "Integrate with GitHub repositories and issues",
        "inputSchema": {
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
    }
]

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "ADOMCP - Hybrid MCP Server",
        "version": "1.0.0", 
        "description": "Azure DevOps and GitHub integration via Model Context Protocol",
        "mcp_compliant": True,
        "transport": "HTTP JSON-RPC 2.0",
        "endpoints": {
            "mcp": "/mcp (GET, POST, OPTIONS)",
            "health": "/health",
            "tools": "/tools",
            "auth": "/api/auth (GET, POST)",
            "secure_keys": "/api/secure-keys (GET, POST)"
        },
        "tools_available": len(MCP_TOOLS),
        "claude_desktop_compatible": True,
        "authentication": {
            "system_available": SECURITY_AVAILABLE,
            "fallback_mode": "environment_variables" if not SECURITY_AVAILABLE else None,
            "registration": "/api/auth (POST with email)",
            "api_key_storage": "/api/secure-keys (authenticated)"
        }
    }

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "server": "ADOMCP", "timestamp": "2025-09-20"}

# Authentication Endpoints
@app.post("/api/auth")
async def register_user(request: Request):
    """User registration and ADOMCP API key generation"""
    if not SECURITY_AVAILABLE or not auth_manager:
        raise HTTPException(status_code=503, detail="Authentication system not available")
    
    try:
        body = await request.json()
        email = body.get("email", "").strip().lower()
        
        if not email or "@" not in email:
            raise HTTPException(status_code=400, detail="Valid email address required")
        
        # Generate ADOMCP API key for the user
        user_token = auth_manager.generate_user_api_key(email)
        
        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": user_token.user_id,
            "api_key": user_token.token,
            "expires_at": user_token.expires_at.isoformat(),
            "instructions": {
                "next_steps": [
                    "Save your API key securely",
                    "Use this key to authenticate when storing platform API keys",
                    "Use /api/secure-keys endpoint to store Azure DevOps and GitHub tokens"
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.get("/api/auth")
async def get_auth_info():
    """Get authentication system information"""
    return {
        "authentication_system": "enabled" if SECURITY_AVAILABLE else "disabled",
        "registration_endpoint": "/api/auth (POST)",
        "api_key_management": "/api/secure-keys",
        "instructions": {
            "registration": "POST to /api/auth with {'email': 'your@email.com'}",
            "api_key_storage": "Use returned API key to store platform tokens at /api/secure-keys"
        }
    }

@app.post("/api/secure-keys")
async def store_platform_keys(request: Request, current_user: Optional[str] = Depends(get_current_user)):
    """Store platform API keys for authenticated user"""
    if not SECURITY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Authentication system not available")
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Valid ADOMCP API key required")
    
    try:
        body = await request.json()
        
        stored_count = 0
        result = {"success": True, "keys_stored": []}
        
        # Store Azure DevOps PAT
        if "azure_devops_pat" in body:
            encrypted_pat = encrypt_api_key_advanced(body["azure_devops_pat"]) if SECURITY_AVAILABLE else body["azure_devops_pat"]
            os.environ[f"USER_{current_user}_AZURE_PAT"] = encrypted_pat
            stored_count += 1
            result["keys_stored"].append("azure_devops_pat")
        
        # Store GitHub Token
        if "github_token" in body:
            encrypted_token = encrypt_api_key_advanced(body["github_token"]) if SECURITY_AVAILABLE else body["github_token"]
            os.environ[f"USER_{current_user}_GITHUB_TOKEN"] = encrypted_token
            stored_count += 1
            result["keys_stored"].append("github_token")
        
        if stored_count == 0:
            raise HTTPException(status_code=400, detail="No valid API keys provided")
        
        result["message"] = f"Successfully stored {stored_count} API key(s)"
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Key storage error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store API keys")

@app.get("/api/secure-keys")
async def get_stored_keys(current_user: Optional[str] = Depends(get_current_user)):
    """Get information about stored API keys for authenticated user"""
    if not SECURITY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Authentication system not available")
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Valid ADOMCP API key required")
    
    stored_keys = []
    if os.getenv(f"USER_{current_user}_AZURE_PAT"):
        stored_keys.append("azure_devops_pat")
    if os.getenv(f"USER_{current_user}_GITHUB_TOKEN"):
        stored_keys.append("github_token")
    
    return {
        "user_id": current_user,
        "stored_keys": stored_keys,
        "instructions": {
            "store_keys": "POST to /api/secure-keys with platform API keys",
            "mcp_usage": "Stored keys will be automatically used by MCP tools"
        }
    }

# MCP Protocol Implementation (Claude Desktop Compatible)
@app.options("/mcp")
async def mcp_options():
    """Handle CORS preflight requests for MCP endpoint"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "86400"
        }
    )

@app.get("/mcp")
async def mcp_info():
    """MCP server information endpoint"""
    return {
        "service": "ADOMCP Hybrid MCP Server",
        "protocol": "JSON-RPC 2.0",
        "version": "1.0.0",
        "capabilities": ["tools"],
        "status": "ready",
        "tools_count": len(MCP_TOOLS),
        "transport": "HTTP",
        "claude_desktop_compatible": True
    }

@app.post("/mcp")
async def mcp_post(request: Request, response: Response):
    """MCP JSON-RPC 2.0 endpoint with full protocol support"""
    # Add CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    try:
        body = await request.json()
        
        # Basic JSON-RPC validation
        if not body.get("jsonrpc") == "2.0":
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC version")
        
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        # Handle MCP methods
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": True
                        }
                    },
                    "serverInfo": {
                        "name": "ADOMCP",
                        "version": "1.0.0"
                    }
                },
                "id": request_id
            }
            
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "tools": MCP_TOOLS
                },
                "id": request_id
            }
            
        elif method == "tools/call":
            # Extract user API key from Authorization header if provided
            user_api_key = None
            try:
                auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer ") and len(auth_header) > 7:
                    user_api_key = auth_header[7:].strip()  # Remove "Bearer " prefix and trim
                    if not user_api_key:  # If empty after trimming
                        user_api_key = None
            except Exception as e:
                logger.debug(f"Auth header parsing error (ignoring): {e}")
                user_api_key = None
            
            return await handle_tool_call(params, request_id, user_api_key)
            
        elif method in ["initialized", "notifications/initialized"]:
            return {"jsonrpc": "2.0", "result": {}, "id": request_id}
            
        elif method == "ping":
            return {"jsonrpc": "2.0", "result": {}, "id": request_id}
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
            
    except Exception as e:
        logger.error(f"MCP endpoint error: {str(e)}")
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            },
            "id": request_id
        }

async def handle_tool_call(params: Dict, request_id: Any, user_api_key: Optional[str] = None) -> Dict:
    """Handle tool call requests with support for both environment variables and user authentication"""
    tool_name = params.get("name")
    tool_arguments = params.get("arguments", {})
    
    # Get API tokens - try user authentication first, then fall back to environment variables
    azure_pat = os.getenv("AZURE_DEVOPS_PAT")
    github_token = os.getenv("GITHUB_TOKEN")
    
    # If user provided API key, try to get their stored tokens
    if user_api_key and SECURITY_AVAILABLE:
        try:
            user_tokens = await get_api_tokens_from_auth(user_api_key)
            if user_tokens and user_tokens.get("azure_pat"):
                azure_pat = user_tokens["azure_pat"]
                logger.info("Using authenticated user's Azure DevOps PAT")
            if user_tokens and user_tokens.get("github_token"):
                github_token = user_tokens["github_token"]
                logger.info("Using authenticated user's GitHub token")
        except Exception as e:
            logger.warning(f"Authentication failed, using environment variables: {str(e)}")
            # Silently fall back to environment variables
    
    try:
        if tool_name == "create_work_item":
            if not azure_pat:
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "❌ Error: AZURE_DEVOPS_PAT environment variable not set"
                            }
                        ]
                    },
                    "id": request_id
                }
            
            azure_api = AzureDevOpsAPI(azure_pat)
            result = await azure_api.create_work_item(
                title=tool_arguments.get("title", "MCP Created Work Item"),
                work_item_type=tool_arguments.get("work_item_type", "User Story"),
                description=tool_arguments.get("description", "Created via MCP tool call"),
                area_path=tool_arguments.get("area_path"),
                iteration_path=tool_arguments.get("iteration_path"),
                assigned_to=tool_arguments.get("assigned_to"),
                tags=tool_arguments.get("tags")
            )
            
            if result["success"]:
                response_text = f"✅ Work item '{tool_arguments.get('title')}' created successfully!\n"
                response_text += f"• Work Item ID: {result['work_item_id']}\n"
                response_text += f"• Type: {result['work_item_type']}\n"
                response_text += f"• URL: {result['work_item_url']}"
            else:
                response_text = f"❌ Failed to create work item: {result['message']}"
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": response_text}]
                },
                "id": request_id
            }
            
        elif tool_name == "update_work_item":
            if not azure_pat:
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "❌ Error: AZURE_DEVOPS_PAT environment variable not set"
                            }
                        ]
                    },
                    "id": request_id
                }
            
            work_item_id = tool_arguments.get("work_item_id")
            if not work_item_id:
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "❌ Error: work_item_id is required for update_work_item"
                            }
                        ]
                    },
                    "id": request_id
                }
            
            azure_api = AzureDevOpsAPI(azure_pat)
            result = await azure_api.update_work_item(
                work_item_id=work_item_id,
                updates=tool_arguments.get("updates", {})
            )
            
            if result["success"]:
                response_text = f"✅ Work item {work_item_id} updated successfully!\n"
                response_text += f"• Fields updated: {result['updates_applied']}\n"
                response_text += f"• URL: {result['work_item_url']}"
            else:
                response_text = f"❌ Failed to update work item: {result['message']}"
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": response_text}]
                },
                "id": request_id
            }
            
        elif tool_name == "github_integration":
            if not github_token:
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "❌ Error: GITHUB_TOKEN environment variable not set"
                            }
                        ]
                    },
                    "id": request_id
                }
            
            github_api = GitHubAPI(github_token)
            action = tool_arguments.get("action", "create_issue")
            
            if action == "create_issue":
                result = await github_api.create_issue(
                    repository=tool_arguments.get("repository", "Jita81/ADOMCP"),
                    title=tool_arguments.get("title", "MCP Created Issue"),
                    description=tool_arguments.get("description", "Created via MCP tool call"),
                    labels=tool_arguments.get("labels", []),
                    assignees=tool_arguments.get("assignees", [])
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
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": response_text}]
                },
                "id": request_id
            }
            
        else:
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"❌ Unknown tool: {tool_name}"
                        }
                    ]
                },
                "id": request_id
            }
            
    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}")
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Tool execution failed: {str(e)}"
            },
            "id": request_id
        }

# Tools endpoint for debugging
@app.get("/tools")
async def list_tools():
    """List available tools for debugging"""
    return {"tools": MCP_TOOLS}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    logger.info(f"🚀 Starting ADOMCP Hybrid MCP Server on port {port}")
    logger.info("🎯 Railway deployment compatible + MCP SDK compliant")
    logger.info("🔗 Claude Desktop ready!")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
