"""
OAuth Authentication Endpoints for ADOMCP
Handles OAuth login, callback, and logout
"""

import json
import sys
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import urllib.parse

# Add security module to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from security.oauth import oauth_manager, get_oauth_providers, generate_oauth_url, handle_oauth_callback

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle OAuth GET requests (login, callback, status)"""
        try:
            # Parse URL and query parameters
            parsed_path = urllib.parse.urlparse(self.path)
            path_parts = parsed_path.path.strip('/').split('/')
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # Add security headers
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('X-XSS-Protection', '1; mode=block')
            
            if len(path_parts) >= 2 and path_parts[1] == 'oauth':
                if len(path_parts) == 2:  # /api/oauth
                    self._handle_oauth_info()
                elif path_parts[2] == 'login':  # /api/oauth/login
                    provider = query_params.get('provider', [None])[0]
                    if provider:
                        self._handle_oauth_login(provider)
                    else:
                        self._handle_oauth_providers()
                elif path_parts[2] == 'callback':  # /api/oauth/callback/{provider}
                    if len(path_parts) >= 4:
                        provider = path_parts[3]
                        code = query_params.get('code', [None])[0]
                        state = query_params.get('state', [None])[0]
                        error = query_params.get('error', [None])[0]
                        self._handle_oauth_callback(provider, code, state, error)
                    else:
                        self._send_error(400, "Provider not specified in callback")
                elif path_parts[2] == 'logout':  # /api/oauth/logout
                    self._handle_oauth_logout()
                elif path_parts[2] == 'status':  # /api/oauth/status
                    self._handle_oauth_status()
                else:
                    self._send_error(404, "OAuth endpoint not found")
            else:
                self._send_error(404, "Invalid OAuth path")
                
        except Exception as e:
            self._send_error(500, f"OAuth request failed: {str(e)}")
    
    def _handle_oauth_info(self):
        """Return OAuth service information"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        providers = get_oauth_providers()
        
        response = {
            "service": "ADOMCP OAuth Authentication",
            "version": "1.0.0",
            "providers": providers,
            "endpoints": {
                "login": "/api/oauth/login?provider={provider}",
                "callback": "/api/oauth/callback/{provider}",
                "logout": "/api/oauth/logout",
                "status": "/api/oauth/status"
            },
            "flow": {
                "step1": "GET /api/oauth/login?provider=github (or google, microsoft)",
                "step2": "User completes OAuth flow on provider site",
                "step3": "Callback returns session token",
                "step4": "Use session token in Authorization header"
            },
            "timestamp": datetime.now().isoformat(),
            "note": "OAuth provides secure, user-friendly authentication"
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def _handle_oauth_providers(self):
        """Return available OAuth providers"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        providers = get_oauth_providers()
        
        response = {
            "available_providers": providers,
            "message": "Choose a provider to login with",
            "login_urls": {
                provider['key']: f"/api/oauth/login?provider={provider['key']}"
                for provider in providers
            },
            "timestamp": datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def _handle_oauth_login(self, provider: str):
        """Initiate OAuth login flow"""
        try:
            auth_url, state_token = generate_oauth_url(provider)
            
            # Return redirect response
            self.send_response(302)
            self.send_header('Location', auth_url)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "redirect",
                "provider": provider,
                "auth_url": auth_url,
                "state": state_token,
                "message": f"Redirecting to {provider} for authentication",
                "timestamp": datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except ValueError as e:
            self._send_error(400, str(e))
        except Exception as e:
            self._send_error(500, f"Failed to initiate OAuth: {str(e)}")
    
    def _handle_oauth_callback(self, provider: str, code: str, state: str, error: str):
        """Handle OAuth callback from provider"""
        if error:
            self._send_oauth_error(error)
            return
        
        if not code or not state:
            self._send_error(400, "Missing code or state parameter")
            return
        
        try:
            success, oauth_token, error_message = handle_oauth_callback(provider, code, state)
            
            if success and oauth_token:
                # Generate session token for client
                session_token = oauth_manager._generate_session_token(oauth_token)
                oauth_manager.active_sessions[session_token] = oauth_token
                
                # Return success page with session token
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                html_response = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ADOMCP - Authentication Successful</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
        .success {{ color: #28a745; }}
        .token {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; word-break: break-all; }}
        .instructions {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <h1 class="success">✅ Authentication Successful!</h1>
    <p>Welcome, <strong>{oauth_token.user_info.get('name', 'User')}</strong>!</p>
    <p>Email: <strong>{oauth_token.user_info.get('email', 'Unknown')}</strong></p>
    <p>Provider: <strong>{oauth_token.provider.title()}</strong></p>
    
    <h3>Your Session Token:</h3>
    <div class="token">
        <code>{session_token}</code>
    </div>
    
    <div class="instructions">
        <h4>How to Use Your Token:</h4>
        <ol>
            <li>Copy the session token above</li>
            <li>Include it in your API requests:</li>
            <li><code>Authorization: Bearer {session_token}</code></li>
            <li>Access secure ADOMCP endpoints</li>
        </ol>
    </div>
    
    <p><strong>Keep this token secure!</strong> It provides access to your ADOMCP resources.</p>
    <p>You can now close this window and use the token in your applications.</p>
    
    <script>
        // Auto-copy token to clipboard
        navigator.clipboard.writeText('{session_token}').then(function() {{
            console.log('Token copied to clipboard');
        }});
    </script>
</body>
</html>
                """
                
                self.wfile.write(html_response.encode())
                
            else:
                self._send_oauth_error(error_message or "Authentication failed")
                
        except Exception as e:
            self._send_error(500, f"OAuth callback failed: {str(e)}")
    
    def _handle_oauth_logout(self):
        """Handle OAuth logout"""
        # Get session token from Authorization header
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            session_token = auth_header[7:]
            logout_success = oauth_manager.logout(session_token)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "success" if logout_success else "not_found",
                "message": "Logged out successfully" if logout_success else "Session not found",
                "timestamp": datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(response).encode())
        else:
            self._send_error(401, "Authorization header required for logout")
    
    def _handle_oauth_status(self):
        """Check OAuth authentication status"""
        # Get session token from Authorization header
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            session_token = auth_header[7:]
            is_valid, user_info, error = oauth_manager.authenticate_request(session_token)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            if is_valid:
                response = {
                    "authenticated": True,
                    "user": user_info,
                    "message": "Session is valid",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                response = {
                    "authenticated": False,
                    "error": error,
                    "message": "Session is invalid",
                    "timestamp": datetime.now().isoformat()
                }
            
            self.wfile.write(json.dumps(response, indent=2).encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "authenticated": False,
                "message": "No authorization header provided",
                "available_providers": get_oauth_providers(),
                "login_info": "Use /api/oauth/login?provider={provider} to authenticate",
                "timestamp": datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(response, indent=2).encode())
    
    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "error": message,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def _send_oauth_error(self, error_message: str):
        """Send OAuth-specific error page"""
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html_response = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ADOMCP - Authentication Failed</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
        .error {{ color: #dc3545; }}
        .retry {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <h1 class="error">❌ Authentication Failed</h1>
    <p><strong>Error:</strong> {error_message}</p>
    
    <div class="retry">
        <h4>Try Again:</h4>
        <ul>
            <li><a href="/api/oauth/login?provider=github">Login with GitHub</a></li>
            <li><a href="/api/oauth/login?provider=google">Login with Google</a></li>
            <li><a href="/api/oauth/login?provider=microsoft">Login with Microsoft</a></li>
        </ul>
    </div>
    
    <p>If the problem persists, please contact support.</p>
</body>
</html>
        """
        
        self.wfile.write(html_response.encode())
