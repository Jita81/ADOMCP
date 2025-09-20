"""
API key management endpoint for Supabase integration
"""

import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get API key information (without exposing actual keys)"""
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        user_id = query_params.get('user_id', [None])[0]
        
        if not user_id:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "error": "user_id parameter is required",
                "example": "/api/keys?user_id=your-unique-id"
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        # In a real implementation, this would query Supabase
        # For now, simulate the response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "user_id": user_id,
            "stored_platforms": ["azure_devops", "github"],  # Simulated
            "message": "API key storage is ready. Use POST to store keys.",
            "timestamp": datetime.now().isoformat(),
            "note": "Actual keys are stored securely and not returned in GET requests"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_POST(self):
        """Store API keys securely"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            user_id = data.get('user_id')
            platform = data.get('platform')
            api_key = data.get('api_key')
            organization_url = data.get('organization_url')
            project_id = data.get('project_id')
            
            if not all([user_id, platform, api_key]):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    "error": "user_id, platform, and api_key are required",
                    "example": {
                        "user_id": "your-unique-id",
                        "platform": "azure_devops",
                        "api_key": "your-pat-token",
                        "organization_url": "https://dev.azure.com/YourOrg",
                        "project_id": "ProjectName"
                    }
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            if platform not in ["azure_devops", "github", "gitlab"]:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    "error": "platform must be one of: azure_devops, github, gitlab"
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # TODO: In a real implementation, store in Supabase here
            # For now, simulate successful storage
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            metadata = {}
            if organization_url:
                metadata["organization_url"] = organization_url
            if project_id:
                metadata["project_id"] = project_id
            
            response = {
                "status": "success",
                "message": f"API key for {platform} stored securely",
                "user_id": user_id,
                "platform": platform,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat(),
                "note": "This is a simulated response. Real implementation would use Supabase."
            }
            
            self.wfile.write(json.dumps(response).encode())
            return
            
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "error": "Invalid JSON in request body"
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "error": f"Internal server error: {str(e)}"
            }
            self.wfile.write(json.dumps(response).encode())
            return
