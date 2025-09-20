"""
Minimal OAuth Test Endpoint - No Dependencies
"""

from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Test OAuth endpoint with minimal dependencies"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "service": "ADOMCP OAuth Test Service",
            "status": "working",
            "timestamp": datetime.now().isoformat(),
            "message": "OAuth endpoint is accessible with Pro plan",
            "test": "success"
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))

    def do_POST(self):
        """Handle POST for test purposes"""
        self.do_GET()
