"""
OAuth Authentication System for ADOMCP
Supports GitHub, Google, and Microsoft OAuth providers
"""

import os
import json
import base64
import secrets
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import urllib.parse
import urllib.request
import logging

logger = logging.getLogger(__name__)

@dataclass
class OAuthProvider:
    """OAuth provider configuration"""
    name: str
    authorize_url: str
    token_url: str
    user_info_url: str
    client_id: str
    client_secret: str
    scopes: list
    redirect_uri: str

@dataclass
class OAuthToken:
    """OAuth token with metadata"""
    access_token: str
    refresh_token: Optional[str]
    expires_at: datetime
    user_info: Dict[str, Any]
    provider: str
    scopes: list

class OAuthManager:
    """
    OAuth authentication manager for ADOMCP
    Handles multiple OAuth providers and token management
    """
    
    def __init__(self, base_url: str = "https://adomcp.vercel.app"):
        self.base_url = base_url
        self.providers = self._setup_providers()
        self.active_sessions: Dict[str, OAuthToken] = {}
        self.state_store: Dict[str, Dict[str, Any]] = {}  # CSRF protection
        
    def _setup_providers(self) -> Dict[str, OAuthProvider]:
        """Setup OAuth providers from environment variables"""
        providers = {}
        
        # GitHub OAuth
        github_client_id = os.getenv('GITHUB_OAUTH_CLIENT_ID')
        github_client_secret = os.getenv('GITHUB_OAUTH_CLIENT_SECRET')
        if github_client_id and github_client_secret:
            providers['github'] = OAuthProvider(
                name='GitHub',
                authorize_url='https://github.com/login/oauth/authorize',
                token_url='https://github.com/login/oauth/access_token',
                user_info_url='https://api.github.com/user',
                client_id=github_client_id,
                client_secret=github_client_secret,
                scopes=['user:email', 'repo'],
                redirect_uri=f"{self.base_url}/api/oauth/callback/github"
            )
        
        # Google OAuth
        google_client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        google_client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
        if google_client_id and google_client_secret:
            providers['google'] = OAuthProvider(
                name='Google',
                authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
                token_url='https://oauth2.googleapis.com/token',
                user_info_url='https://www.googleapis.com/oauth2/v2/userinfo',
                client_id=google_client_id,
                client_secret=google_client_secret,
                scopes=['openid', 'email', 'profile'],
                redirect_uri=f"{self.base_url}/api/oauth/callback/google"
            )
        
        # Microsoft OAuth (Azure AD)
        microsoft_client_id = os.getenv('MICROSOFT_OAUTH_CLIENT_ID')
        microsoft_client_secret = os.getenv('MICROSOFT_OAUTH_CLIENT_SECRET')
        if microsoft_client_id and microsoft_client_secret:
            providers['microsoft'] = OAuthProvider(
                name='Microsoft',
                authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
                user_info_url='https://graph.microsoft.com/v1.0/me',
                client_id=microsoft_client_id,
                client_secret=microsoft_client_secret,
                scopes=['openid', 'email', 'profile', 'User.Read'],
                redirect_uri=f"{self.base_url}/api/oauth/callback/microsoft"
            )
        
        return providers
    
    def get_available_providers(self) -> list:
        """Get list of configured OAuth providers"""
        return [
            {
                'name': provider.name,
                'key': key,
                'configured': True
            }
            for key, provider in self.providers.items()
        ]
    
    def generate_authorization_url(self, provider_key: str, user_state: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate OAuth authorization URL with CSRF protection
        Returns: (authorization_url, state_token)
        """
        if provider_key not in self.providers:
            raise ValueError(f"Provider '{provider_key}' not configured")
        
        provider = self.providers[provider_key]
        
        # Generate CSRF state token
        state_token = secrets.token_urlsafe(32)
        
        # Store state for validation
        self.state_store[state_token] = {
            'provider': provider_key,
            'created_at': datetime.now(),
            'user_state': user_state,
            'expires_at': datetime.now() + timedelta(minutes=10)
        }
        
        # Build authorization URL
        params = {
            'client_id': provider.client_id,
            'redirect_uri': provider.redirect_uri,
            'scope': ' '.join(provider.scopes),
            'response_type': 'code',
            'state': state_token,
            'access_type': 'offline',  # For refresh tokens
            'prompt': 'consent'  # Ensure we get refresh token
        }
        
        auth_url = f"{provider.authorize_url}?{urllib.parse.urlencode(params)}"
        
        return auth_url, state_token
    
    def handle_oauth_callback(self, provider_key: str, code: str, state: str) -> Tuple[bool, Optional[OAuthToken], Optional[str]]:
        """
        Handle OAuth callback and exchange code for tokens
        Returns: (success, oauth_token, error_message)
        """
        try:
            # Validate state (CSRF protection)
            if state not in self.state_store:
                return False, None, "Invalid state parameter (CSRF protection)"
            
            state_data = self.state_store[state]
            if datetime.now() > state_data['expires_at']:
                del self.state_store[state]
                return False, None, "State expired"
            
            if state_data['provider'] != provider_key:
                return False, None, "Provider mismatch"
            
            # Clean up state
            del self.state_store[state]
            
            if provider_key not in self.providers:
                return False, None, f"Provider '{provider_key}' not configured"
            
            provider = self.providers[provider_key]
            
            # Exchange code for tokens
            token_data = self._exchange_code_for_tokens(provider, code)
            if not token_data:
                return False, None, "Failed to exchange code for tokens"
            
            # Get user information
            user_info = self._get_user_info(provider, token_data['access_token'])
            if not user_info:
                return False, None, "Failed to get user information"
            
            # Create OAuth token
            expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
            oauth_token = OAuthToken(
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                expires_at=expires_at,
                user_info=user_info,
                provider=provider_key,
                scopes=provider.scopes
            )
            
            # Generate session token
            session_token = self._generate_session_token(oauth_token)
            self.active_sessions[session_token] = oauth_token
            
            logger.info(f"OAuth authentication successful for {user_info.get('email', 'unknown')} via {provider_key}")
            
            return True, oauth_token, None
            
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return False, None, f"Authentication failed: {str(e)}"
    
    def _exchange_code_for_tokens(self, provider: OAuthProvider, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access tokens"""
        try:
            data = {
                'client_id': provider.client_id,
                'client_secret': provider.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': provider.redirect_uri
            }
            
            req_data = urllib.parse.urlencode(data).encode('utf-8')
            request = urllib.request.Request(
                provider.token_url,
                data=req_data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
            )
            
            with urllib.request.urlopen(request) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return None
    
    def _get_user_info(self, provider: OAuthProvider, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information using access token"""
        try:
            request = urllib.request.Request(
                provider.user_info_url,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Accept': 'application/json'
                }
            )
            
            with urllib.request.urlopen(request) as response:
                response_data = response.read().decode('utf-8')
                user_data = json.loads(response_data)
                
                # Normalize user data across providers
                normalized = {
                    'id': str(user_data.get('id', user_data.get('sub', ''))),
                    'email': user_data.get('email', ''),
                    'name': user_data.get('name', user_data.get('login', '')),
                    'avatar_url': user_data.get('avatar_url', user_data.get('picture', '')),
                    'provider': provider.name.lower(),
                    'raw_data': user_data
                }
                
                return normalized
                
        except Exception as e:
            logger.error(f"User info error: {e}")
            return None
    
    def _generate_session_token(self, oauth_token: OAuthToken) -> str:
        """Generate session token for authenticated user"""
        user_id = oauth_token.user_info.get('id', '')
        email = oauth_token.user_info.get('email', '')
        provider = oauth_token.provider
        timestamp = str(int(time.time()))
        
        # Create token payload
        payload = f"{user_id}:{email}:{provider}:{timestamp}"
        token_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]
        
        session_token = f"adomcp_oauth_{provider}_{token_hash}_{timestamp}"
        return session_token
    
    def authenticate_request(self, session_token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate request using OAuth session token
        Returns: (is_valid, user_info, error_message)
        """
        if not session_token:
            return False, None, "No session token provided"
        
        if not session_token.startswith('adomcp_oauth_'):
            return False, None, "Invalid session token format"
        
        if session_token not in self.active_sessions:
            return False, None, "Invalid or expired session token"
        
        oauth_token = self.active_sessions[session_token]
        
        # Check if token is expired
        if datetime.now() > oauth_token.expires_at:
            # Try to refresh if we have a refresh token
            if oauth_token.refresh_token:
                refreshed = self._refresh_oauth_token(session_token)
                if not refreshed:
                    del self.active_sessions[session_token]
                    return False, None, "Session expired and refresh failed"
            else:
                del self.active_sessions[session_token]
                return False, None, "Session expired"
        
        return True, oauth_token.user_info, None
    
    def _refresh_oauth_token(self, session_token: str) -> bool:
        """Refresh OAuth token using refresh token"""
        if session_token not in self.active_sessions:
            return False
        
        oauth_token = self.active_sessions[session_token]
        if not oauth_token.refresh_token:
            return False
        
        provider = self.providers.get(oauth_token.provider)
        if not provider:
            return False
        
        try:
            data = {
                'client_id': provider.client_id,
                'client_secret': provider.client_secret,
                'refresh_token': oauth_token.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            req_data = urllib.parse.urlencode(data).encode('utf-8')
            request = urllib.request.Request(
                provider.token_url,
                data=req_data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
            )
            
            with urllib.request.urlopen(request) as response:
                response_data = response.read().decode('utf-8')
                token_data = json.loads(response_data)
            
            # Update the session with new tokens
            oauth_token.access_token = token_data['access_token']
            if 'refresh_token' in token_data:
                oauth_token.refresh_token = token_data['refresh_token']
            oauth_token.expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
            
            logger.info(f"OAuth token refreshed for user {oauth_token.user_info.get('email', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False
    
    def logout(self, session_token: str) -> bool:
        """Logout user and invalidate session"""
        if session_token in self.active_sessions:
            oauth_token = self.active_sessions[session_token]
            user_email = oauth_token.user_info.get('email', 'unknown')
            del self.active_sessions[session_token]
            logger.info(f"User logged out: {user_email}")
            return True
        return False
    
    def get_user_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active sessions (for admin/debugging)"""
        sessions = {}
        for token, oauth_token in self.active_sessions.items():
            sessions[token[:20] + '...'] = {
                'user_email': oauth_token.user_info.get('email', 'unknown'),
                'provider': oauth_token.provider,
                'expires_at': oauth_token.expires_at.isoformat(),
                'scopes': oauth_token.scopes
            }
        return sessions

# Global OAuth manager instance
oauth_manager = OAuthManager()

def get_oauth_providers() -> list:
    """Get available OAuth providers"""
    return oauth_manager.get_available_providers()

def generate_oauth_url(provider: str, user_state: str = None) -> Tuple[str, str]:
    """Generate OAuth authorization URL"""
    return oauth_manager.generate_authorization_url(provider, user_state)

def handle_oauth_callback(provider: str, code: str, state: str) -> Tuple[bool, Optional[OAuthToken], Optional[str]]:
    """Handle OAuth callback"""
    return oauth_manager.handle_oauth_callback(provider, code, state)

def authenticate_oauth_request(session_token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Authenticate request using OAuth session token"""
    return oauth_manager.authenticate_request(session_token)
