"""
Comprehensive input validation and security module for ADOMCP
Implements JSON schema validation, sanitization, and security checks
"""

import json
import re
import html
import uuid
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime
import urllib.parse

# JSON Schema definitions for API endpoints
WORK_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string", 
            "minLength": 1, 
            "maxLength": 255,
            "pattern": "^[^<>\"&]*$"  # No HTML/script tags
        },
        "description": {
            "type": "string", 
            "maxLength": 10000
        },
        "work_item_type": {
            "type": "string",
            "enum": ["Epic", "Feature", "User Story", "Task", "Bug", "Issue"]
        },
        "fields": {
            "type": "object",
            "additionalProperties": {
                "anyOf": [
                    {"type": "string", "maxLength": 1000},
                    {"type": "number"},
                    {"type": "boolean"}
                ]
            }
        }
    },
    "required": ["title", "work_item_type"],
    "additionalProperties": False
}

AZURE_DEVOPS_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "organization_url": {
            "type": "string",
            "pattern": "^https://dev\\.azure\\.com/[a-zA-Z0-9_-]+/?$"
        },
        "pat_token": {
            "type": "string",
            "minLength": 20,
            "maxLength": 200,
            "pattern": "^[A-Za-z0-9+/=]+$"  # Base64 pattern
        },
        "project": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
            "pattern": "^[a-zA-Z0-9_-]+$|^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        }
    },
    "required": ["organization_url", "pat_token", "project"],
    "additionalProperties": False
}

GITHUB_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "github_token": {
            "type": "string",
            "pattern": "^(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})$"
        },
        "repository": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$"
        }
    },
    "required": ["github_token", "repository"],
    "additionalProperties": False
}

API_KEY_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {
            "type": "string",
            "minLength": 3,
            "maxLength": 100,
            "pattern": "^[a-zA-Z0-9_-]+$"
        },
        "platform": {
            "type": "string",
            "enum": ["azure_devops", "github", "gitlab"]
        },
        "api_key": {
            "type": "string",
            "minLength": 10,
            "maxLength": 500
        },
        "organization_url": {
            "type": "string",
            "maxLength": 200
        },
        "project_id": {
            "type": "string",
            "maxLength": 100
        }
    },
    "required": ["user_id", "platform", "api_key"],
    "additionalProperties": False
}

MCP_JSONRPC_SCHEMA = {
    "type": "object",
    "properties": {
        "jsonrpc": {
            "type": "string",
            "enum": ["2.0"]
        },
        "method": {
            "type": "string",
            "enum": ["tools/list", "tools/call", "initialize"]
        },
        "params": {
            "type": "object"
        },
        "id": {
            "anyOf": [
                {"type": "string"},
                {"type": "number"},
                {"type": "null"}
            ]
        }
    },
    "required": ["jsonrpc", "method"],
    "additionalProperties": False
}

class SecurityValidator:
    """Comprehensive security validation for ADOMCP"""
    
    def __init__(self):
        self.correlation_id = str(uuid.uuid4())
        
    def generate_correlation_id(self) -> str:
        """Generate unique correlation ID for request tracking"""
        return str(uuid.uuid4())
    
    def validate_json_schema(self, data: Dict[Any, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate data against JSON schema"""
        try:
            # Simple validation since jsonschema package may not be available
            return self._validate_schema_manually(data, schema)
        except Exception as e:
            return False, f"Schema validation error: {str(e)}"
    
    def _validate_schema_manually(self, data: Dict[Any, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Manual schema validation implementation"""
        if schema.get("type") == "object":
            if not isinstance(data, dict):
                return False, "Expected object type"
            
            # Check required fields
            required = schema.get("required", [])
            for field in required:
                if field not in data:
                    return False, f"Missing required field: {field}"
            
            # Check properties
            properties = schema.get("properties", {})
            for key, value in data.items():
                if key in properties:
                    valid, error = self._validate_property(value, properties[key])
                    if not valid:
                        return False, f"Field '{key}': {error}"
                elif not schema.get("additionalProperties", True):
                    return False, f"Additional property not allowed: {key}"
        
        return True, None
    
    def _validate_property(self, value: Any, prop_schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate individual property against schema"""
        prop_type = prop_schema.get("type")
        
        if prop_type == "string":
            if not isinstance(value, str):
                return False, "Expected string type"
            
            min_len = prop_schema.get("minLength", 0)
            max_len = prop_schema.get("maxLength", float('inf'))
            
            if len(value) < min_len:
                return False, f"String too short (min: {min_len})"
            if len(value) > max_len:
                return False, f"String too long (max: {max_len})"
            
            pattern = prop_schema.get("pattern")
            if pattern and not re.match(pattern, value):
                return False, "String format invalid"
            
            enum_values = prop_schema.get("enum")
            if enum_values and value not in enum_values:
                return False, f"Value must be one of: {enum_values}"
        
        elif prop_type == "number":
            if not isinstance(value, (int, float)):
                return False, "Expected number type"
        
        elif prop_type == "boolean":
            if not isinstance(value, bool):
                return False, "Expected boolean type"
        
        elif prop_type == "object":
            if not isinstance(value, dict):
                return False, "Expected object type"
            return self._validate_schema_manually(value, prop_schema)
        
        return True, None
    
    def sanitize_string(self, text: str) -> str:
        """Sanitize string input to prevent XSS and injection attacks"""
        if not isinstance(text, str):
            return str(text)
        
        # HTML escape
        text = html.escape(text)
        
        # Remove potential script tags and suspicious patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'onclick='
        ]
        
        for pattern in dangerous_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text.strip()
    
    def validate_work_item_data(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Validate and sanitize work item data"""
        # Schema validation
        valid, error = self.validate_json_schema(data, WORK_ITEM_SCHEMA)
        if not valid:
            return False, error, {}
        
        # Sanitize strings
        sanitized_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized_data[key] = self.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized_data[key] = {
                    k: self.sanitize_string(v) if isinstance(v, str) else v
                    for k, v in value.items()
                }
            else:
                sanitized_data[key] = value
        
        return True, None, sanitized_data
    
    def validate_azure_devops_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate Azure DevOps configuration"""
        return self.validate_json_schema(config, AZURE_DEVOPS_CONFIG_SCHEMA)
    
    def validate_github_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate GitHub configuration"""
        return self.validate_json_schema(config, GITHUB_CONFIG_SCHEMA)
    
    def validate_api_key_data(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Validate and sanitize API key storage data"""
        # Schema validation
        valid, error = self.validate_json_schema(data, API_KEY_SCHEMA)
        if not valid:
            return False, error, {}
        
        # Additional security checks
        user_id = data.get('user_id', '')
        if len(user_id) < 3:
            return False, "User ID too short (minimum 3 characters)", {}
        
        # Sanitize user_id specifically
        sanitized_user_id = re.sub(r'[^a-zA-Z0-9_-]', '', user_id)
        if sanitized_user_id != user_id:
            return False, "User ID contains invalid characters", {}
        
        # Don't log or expose API keys in any validation
        sanitized_data = data.copy()
        return True, None, sanitized_data
    
    def validate_mcp_request(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate MCP JSON-RPC request"""
        return self.validate_json_schema(data, MCP_JSONRPC_SCHEMA)
    
    def validate_wiql_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """Basic WIQL query validation to prevent injection"""
        if not isinstance(query, str):
            return False, "WIQL query must be a string"
        
        if len(query) > 5000:
            return False, "WIQL query too long (max 5000 characters)"
        
        # Check for dangerous SQL-like patterns
        dangerous_patterns = [
            r';\s*(drop|delete|insert|update|create|alter)\s+',
            r'--',
            r'/\*.*?\*/',
            r'xp_cmdshell',
            r'sp_executesql'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, "WIQL query contains potentially dangerous patterns"
        
        # Must contain basic WIQL structure
        if not re.search(r'select\s+.*\s+from\s+workitems', query, re.IGNORECASE):
            return False, "Invalid WIQL query structure"
        
        return True, None
    
    def create_safe_error_response(self, error: Exception, correlation_id: str, context: str = "") -> Dict[str, Any]:
        """Create safe error response without exposing internal details"""
        
        # Log detailed error internally (would go to logging system)
        error_details = {
            "correlation_id": correlation_id,
            "context": context,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        
        # Return safe response to client
        safe_response = {
            "error": "Internal server error",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "message": "Please contact support with the correlation ID if this issue persists"
        }
        
        # For specific known safe errors, provide more detail
        if isinstance(error, (ValueError, TypeError)) and "validation" in str(error).lower():
            safe_response["error"] = "Validation error"
            safe_response["message"] = "The request data is invalid. Please check your input format."
        
        return safe_response
    
    def validate_request_size(self, content_length: int, max_size: int = 1024 * 1024) -> Tuple[bool, Optional[str]]:
        """Validate request size to prevent DoS attacks"""
        if content_length > max_size:
            return False, f"Request too large (max: {max_size} bytes)"
        return True, None
