"""
Main entrypoint for Vercel deployment
"""

from datetime import datetime
from http.server import BaseHTTPRequestHandler
import json
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        
        if path == '/' or path == '/index':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
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
                "docs": "Use /api/capabilities to see available tools"
            }
            
        elif path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "Azure DevOps Multi-Platform MCP"
            }
            
        elif path == '/test':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "message": "Use /api/test for the actual API test endpoint",
                "redirect": "/api/test",
                "timestamp": datetime.now().isoformat()
            }
            
        elif path == '/capabilities':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "message": "Use /api/capabilities for the actual capabilities endpoint",
                "redirect": "/api/capabilities", 
                "timestamp": datetime.now().isoformat()
            }
            
        elif path == '/mcp':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "message": "Use /api/mcp for the actual MCP endpoint",
                "redirect": "/api/mcp",
                "timestamp": datetime.now().isoformat()
            }
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "error": "Not Found",
                "path": path,
                "available_endpoints": ["/", "/health", "/api/test", "/api/capabilities", "/api/mcp"],
                "timestamp": datetime.now().isoformat()
            }
        
        self.wfile.write(json.dumps(response).encode())
        return
