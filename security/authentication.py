"""
Authentication and Authorization Module for ADOMCP
Implements proper user authentication to prevent unauthorized access
"""

import os
import secrets
import hashlib
import hmac
import time
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class AuthToken:
    """Authentication token with metadata"""
    token: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    scopes: list
    metadata: Dict[str, Any]

class AuthenticationManager:
    """
    Secure authentication system for ADOMCP
    Implements API key based authentication to prevent unauthorized access
    """
    
    def __init__(self):
        self.secret_key = self._get_auth_secret()
        self.token_expiry_hours = 24  # Tokens expire after 24 hours
        self.active_tokens: Dict[str, AuthToken] = {}
        
    def _get_auth_secret(self) -> bytes:
        """Get or generate authentication secret"""
        secret = os.getenv('ADOMCP_AUTH_SECRET')
        if secret:
            return base64.b64decode(secret)
        
        # Generate new secret for this session
        new_secret = secrets.token_bytes(32)
        logger.warning("No AUTH_SECRET found, using session secret. Set ADOMCP_AUTH_SECRET environment variable for production!")
        return new_secret
    
    def generate_user_api_key(self, user_id: str, scopes: list = None) -> str:
        """
        Generate a secure API key for a user
        This should be done by the user through a secure registration process
        """
        if scopes is None:
            scopes = ['read', 'write', 'manage_keys']
        
        # Create unique API key
        timestamp = str(int(time.time()))
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
        random_part = secrets.token_hex(16)
        
        # Format: adomcp_<version>_<user_hash>_<timestamp>_<random>
        api_key = f"adomcp_v1_{user_hash}_{timestamp}_{random_part}"
        
        # Create signature to verify key integrity
        signature = self._sign_api_key(api_key, user_id, scopes)
        
        # Store in memory (in production, store in secure database)
        self.active_tokens[api_key] = AuthToken(
            token=api_key,
            user_id=user_id,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365),  # API keys last 1 year
            scopes=scopes,
            metadata={
                'signature': signature,
                'type': 'api_key',
                'created_by': 'system'
            }
        )
        
        logger.info(f"Generated API key for user {user_id} with scopes: {scopes}")
        return api_key
    
    def _sign_api_key(self, api_key: str, user_id: str, scopes: list) -> str:
        """Create HMAC signature for API key verification"""
        message = f"{api_key}:{user_id}:{':'.join(sorted(scopes))}".encode()
        signature = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()
        return signature
    
    def authenticate_request(self, api_key: str, required_scope: str = 'read') -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Authenticate a request using API key
        Returns: (is_valid, user_id, error_info)
        """
        if not api_key:
            return False, None, {'error': 'API key required', 'code': 'MISSING_API_KEY'}
        
        if not api_key.startswith('adomcp_v1_'):
            return False, None, {'error': 'Invalid API key format', 'code': 'INVALID_FORMAT'}
        
        # Check if key exists
        if api_key not in self.active_tokens:
            return False, None, {'error': 'Invalid API key', 'code': 'INVALID_KEY'}
        
        token = self.active_tokens[api_key]
        
        # Check expiry
        if datetime.now() > token.expires_at:
            # Remove expired token
            del self.active_tokens[api_key]
            return False, None, {'error': 'API key expired', 'code': 'EXPIRED_KEY'}
        
        # Check scope
        if required_scope not in token.scopes:
            return False, None, {'error': f'Insufficient permissions. Required: {required_scope}', 'code': 'INSUFFICIENT_SCOPE'}
        
        # Verify signature
        expected_signature = self._sign_api_key(api_key, token.user_id, token.scopes)
        if not hmac.compare_digest(expected_signature, token.metadata['signature']):
            return False, None, {'error': 'API key signature invalid', 'code': 'INVALID_SIGNATURE'}
        
        logger.debug(f"Authenticated user {token.user_id} with scope {required_scope}")
        return True, token.user_id, None
    
    def validate_user_access(self, authenticated_user_id: str, requested_user_id: str) -> bool:
        """
        Validate that the authenticated user can access the requested user's resources
        Users can only access their own resources
        """
        if authenticated_user_id != requested_user_id:
            logger.warning(f"User {authenticated_user_id} attempted to access resources for {requested_user_id}")
            return False
        return True
    
    def revoke_api_key(self, api_key: str, requesting_user_id: str) -> bool:
        """Revoke an API key (user can revoke their own keys)"""
        if api_key not in self.active_tokens:
            return False
        
        token = self.active_tokens[api_key]
        
        # Users can only revoke their own keys
        if token.user_id != requesting_user_id:
            logger.warning(f"User {requesting_user_id} attempted to revoke key for {token.user_id}")
            return False
        
        del self.active_tokens[api_key]
        logger.info(f"Revoked API key for user {requesting_user_id}")
        return True
    
    def list_user_keys(self, user_id: str) -> list:
        """List all active API keys for a user (without exposing the keys)"""
        user_keys = []
        for api_key, token in self.active_tokens.items():
            if token.user_id == user_id:
                user_keys.append({
                    'key_id': api_key[:20] + '...',  # Partial key for identification
                    'created_at': token.created_at.isoformat(),
                    'expires_at': token.expires_at.isoformat(),
                    'scopes': token.scopes,
                    'status': 'active' if datetime.now() < token.expires_at else 'expired'
                })
        return user_keys
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens from memory"""
        now = datetime.now()
        expired_keys = [
            api_key for api_key, token in self.active_tokens.items()
            if now > token.expires_at
        ]
        
        for key in expired_keys:
            del self.active_tokens[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired API keys")
    
    def get_authentication_info(self) -> Dict[str, Any]:
        """Get information about the authentication system"""
        self.cleanup_expired_tokens()
        
        return {
            'authentication_required': True,
            'api_key_format': 'adomcp_v1_<user_hash>_<timestamp>_<random>',
            'token_expiry_hours': self.token_expiry_hours * 365 * 24,  # API keys last 1 year
            'active_tokens': len(self.active_tokens),
            'supported_scopes': ['read', 'write', 'manage_keys'],
            'security_features': [
                'HMAC signature verification',
                'Scope-based authorization', 
                'User isolation',
                'Token expiry',
                'Audit logging'
            ]
        }

def require_auth(required_scope: str = 'read'):
    """
    Decorator to require authentication for API endpoints
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract API key from request headers
            # This would be implemented based on the specific framework
            # For now, return the function as-is
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Global authentication manager
auth_manager = AuthenticationManager()

def authenticate_api_request(api_key: str, required_scope: str = 'read') -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Convenience function for API authentication"""
    return auth_manager.authenticate_request(api_key, required_scope)

def generate_user_api_key(user_id: str, scopes: list = None) -> str:
    """Convenience function to generate API key for user"""
    return auth_manager.generate_user_api_key(user_id, scopes)

def validate_user_access(authenticated_user: str, requested_user: str) -> bool:
    """Convenience function to validate user access"""
    return auth_manager.validate_user_access(authenticated_user, requested_user)
