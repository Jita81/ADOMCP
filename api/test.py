"""
API test endpoint for Vercel
"""

from datetime import datetime
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "test": "success",
            "message": "External API access verified",
            "timestamp": datetime.now().isoformat(),
            "deployment": "vercel",
            "endpoint": "/api/test"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return