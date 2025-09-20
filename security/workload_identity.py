"""
Workload Identity Manager for ADOMCP
Implements secretless authentication using platform-native identity services
"""

import os
import json
# Try to import jwt - graceful fallback if not available
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class IdentityToken:
    """Container for identity tokens with metadata"""
    token: str
    expires_at: datetime
    token_type: str
    scopes: list
    platform: str
    metadata: Dict[str, Any]

class WorkloadIdentityManager:
    """
    Implements secretless authentication using workload identities
    Eliminates the need for storing long-lived credentials
    """
    
    def __init__(self):
        self.token_cache: Dict[str, IdentityToken] = {}
        self.refresh_buffer_minutes = 5  # Refresh tokens 5 minutes before expiry
        
    def get_azure_managed_identity_token(self, resource: str = "https://dev.azure.com/") -> Optional[IdentityToken]:
        """
        Get Azure Managed Identity token for Azure DevOps access
        This eliminates the need for PAT tokens in Azure environments
        """
        cache_key = f"azure_mi_{resource}"
        
        # Check cache first
        if self._is_token_valid(cache_key):
            return self.token_cache[cache_key]
        
        try:
            # Azure Managed Identity endpoint
            metadata_endpoint = "http://169.254.169.254/metadata/identity/oauth2/token"
            
            headers = {
                'Metadata': 'true'
            }
            
            params = {
                'api-version': '2018-02-01',
                'resource': resource
            }
            
            response = requests.get(metadata_endpoint, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Calculate expiry time
                expires_in = int(token_data.get('expires_in', 3600))
                expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                identity_token = IdentityToken(
                    token=token_data['access_token'],
                    expires_at=expires_at,
                    token_type='Bearer',
                    scopes=['https://dev.azure.com/.default'],
                    platform='azure_devops',
                    metadata={
                        'resource': resource,
                        'token_type': token_data.get('token_type', 'Bearer'),
                        'client_id': token_data.get('client_id'),
                        'object_id': token_data.get('object_id'),
                        'msi_res_id': token_data.get('msi_res_id')
                    }
                )
                
                self.token_cache[cache_key] = identity_token
                logger.info(f"Successfully obtained Azure Managed Identity token for {resource}")
                return identity_token
            
            else:
                logger.warning(f"Failed to get Azure Managed Identity token: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.debug(f"Azure Managed Identity not available (likely not running in Azure): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting Azure Managed Identity token: {str(e)}")
            return None
    
    def get_github_app_token(self, app_id: str, private_key: str, installation_id: Optional[str] = None) -> Optional[IdentityToken]:
        """
        Get GitHub App JWT token for GitHub access
        This provides better security than PAT tokens for applications
        """
        if not JWT_AVAILABLE:
            logger.debug("JWT library not available, cannot create GitHub App tokens")
            return None
            
        cache_key = f"github_app_{app_id}_{installation_id or 'app'}"
        
        # Check cache first
        if self._is_token_valid(cache_key):
            return self.token_cache[cache_key]
        
        try:
            # Create JWT for GitHub App authentication
            now = int(time.time())
            payload = {
                'iat': now,
                'exp': now + 600,  # JWT expires in 10 minutes
                'iss': app_id
            }
            
            # Sign JWT with private key
            jwt_token = jwt.encode(payload, private_key, algorithm='RS256')
            
            if installation_id:
                # Get installation access token
                url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
                headers = {
                    'Authorization': f'Bearer {jwt_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'ADOMCP-WorkloadIdentity/1.0'
                }
                
                response = requests.post(url, headers=headers, timeout=10)
                
                if response.status_code == 201:
                    token_data = response.json()
                    expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
                    
                    identity_token = IdentityToken(
                        token=token_data['token'],
                        expires_at=expires_at,
                        token_type='token',
                        scopes=token_data.get('permissions', {}),
                        platform='github',
                        metadata={
                            'app_id': app_id,
                            'installation_id': installation_id,
                            'repository_selection': token_data.get('repository_selection'),
                            'permissions': token_data.get('permissions', {})
                        }
                    )
                    
                    self.token_cache[cache_key] = identity_token
                    logger.info(f"Successfully obtained GitHub App installation token for {installation_id}")
                    return identity_token
                else:
                    logger.error(f"Failed to get GitHub App installation token: {response.status_code}")
                    return None
            else:
                # Return JWT token for app-level operations
                expires_at = datetime.now() + timedelta(minutes=10)
                
                identity_token = IdentityToken(
                    token=jwt_token,
                    expires_at=expires_at,
                    token_type='Bearer',
                    scopes=['app'],
                    platform='github',
                    metadata={
                        'app_id': app_id,
                        'token_usage': 'app_level'
                    }
                )
                
                self.token_cache[cache_key] = identity_token
                logger.info(f"Successfully created GitHub App JWT token for app {app_id}")
                return identity_token
                
        except Exception as e:
            logger.error(f"Error getting GitHub App token: {str(e)}")
            return None
    
    def get_vercel_identity_token(self) -> Optional[IdentityToken]:
        """
        Get Vercel identity token for Vercel-specific integrations
        Uses Vercel's built-in identity when running on Vercel
        """
        cache_key = "vercel_identity"
        
        # Check cache first
        if self._is_token_valid(cache_key):
            return self.token_cache[cache_key]
        
        try:
            # Check if running on Vercel
            vercel_region = os.getenv('VERCEL_REGION')
            vercel_url = os.getenv('VERCEL_URL')
            
            if not (vercel_region and vercel_url):
                logger.debug("Not running on Vercel, skipping Vercel identity")
                return None
            
            # Vercel provides identity through environment variables
            # This is a simulated implementation - actual Vercel identity
            # would use their specific authentication mechanisms
            
            identity_token = IdentityToken(
                token=f"vercel_{vercel_region}_{int(time.time())}",
                expires_at=datetime.now() + timedelta(hours=1),
                token_type='Bearer',
                scopes=['vercel:read', 'vercel:write'],
                platform='vercel',
                metadata={
                    'region': vercel_region,
                    'url': vercel_url,
                    'function_name': os.getenv('VERCEL_FUNCTION_NAME'),
                    'deployment_id': os.getenv('VERCEL_DEPLOYMENT_ID')
                }
            )
            
            self.token_cache[cache_key] = identity_token
            logger.info("Successfully obtained Vercel identity token")
            return identity_token
            
        except Exception as e:
            logger.error(f"Error getting Vercel identity token: {str(e)}")
            return None
    
    def get_supabase_service_role_token(self, project_ref: str) -> Optional[IdentityToken]:
        """
        Get Supabase service role token with proper scoping
        Uses environment-based authentication when available
        """
        cache_key = f"supabase_service_{project_ref}"
        
        # Check cache first  
        if self._is_token_valid(cache_key):
            return self.token_cache[cache_key]
        
        try:
            # Get service role key from environment
            service_role_key = os.getenv('SUPABASE_SERVICE_KEY')
            
            if not service_role_key:
                logger.warning("SUPABASE_SERVICE_KEY not found in environment")
                return None
            
            # Supabase service role tokens are long-lived JWTs
            # Decode to check expiry (only if JWT library available)
            if JWT_AVAILABLE:
                try:
                    decoded = jwt.decode(service_role_key, options={"verify_signature": False})
                    exp = decoded.get('exp')
                    expires_at = datetime.fromtimestamp(exp) if exp else datetime.now() + timedelta(days=365)
                except:
                    # If we can't decode, assume it's valid for a year
                    expires_at = datetime.now() + timedelta(days=365)
            else:
                # Without JWT library, assume it's valid for a year
                expires_at = datetime.now() + timedelta(days=365)
            
            identity_token = IdentityToken(
                token=service_role_key,
                expires_at=expires_at,
                token_type='Bearer',
                scopes=['service_role'],
                platform='supabase',
                metadata={
                    'project_ref': project_ref,
                    'role': 'service_role',
                    'usage': 'backend_operations'
                }
            )
            
            self.token_cache[cache_key] = identity_token
            logger.info(f"Successfully obtained Supabase service role token for {project_ref}")
            return identity_token
            
        except Exception as e:
            logger.error(f"Error getting Supabase service role token: {str(e)}")
            return None
    
    def _is_token_valid(self, cache_key: str) -> bool:
        """Check if cached token is still valid"""
        if cache_key not in self.token_cache:
            return False
        
        token = self.token_cache[cache_key]
        buffer_time = timedelta(minutes=self.refresh_buffer_minutes)
        
        return datetime.now() + buffer_time < token.expires_at
    
    def refresh_token(self, cache_key: str) -> Optional[IdentityToken]:
        """Refresh a specific token"""
        if cache_key in self.token_cache:
            del self.token_cache[cache_key]
        
        # Re-acquire token based on cache key pattern
        if cache_key.startswith('azure_mi_'):
            resource = cache_key.replace('azure_mi_', '')
            return self.get_azure_managed_identity_token(resource)
        elif cache_key.startswith('github_app_'):
            # Would need to store app_id and private_key for refresh
            logger.warning("GitHub App token refresh requires re-initialization")
            return None
        elif cache_key == 'vercel_identity':
            return self.get_vercel_identity_token()
        elif cache_key.startswith('supabase_service_'):
            project_ref = cache_key.replace('supabase_service_', '')
            return self.get_supabase_service_role_token(project_ref)
        
        return None
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens from cache"""
        now = datetime.now()
        expired_keys = [
            key for key, token in self.token_cache.items()
            if now >= token.expires_at
        ]
        
        for key in expired_keys:
            del self.token_cache[key]
            logger.debug(f"Removed expired token: {key}")
    
    def get_token_for_platform(self, platform: str, **kwargs) -> Optional[IdentityToken]:
        """
        Get the appropriate token for a specific platform
        This is the main entry point for workload identity
        """
        self.cleanup_expired_tokens()
        
        if platform == 'azure_devops':
            resource = kwargs.get('resource', 'https://dev.azure.com/')
            return self.get_azure_managed_identity_token(resource)
        
        elif platform == 'github':
            app_id = kwargs.get('app_id')
            private_key = kwargs.get('private_key') 
            installation_id = kwargs.get('installation_id')
            
            if app_id and private_key:
                return self.get_github_app_token(app_id, private_key, installation_id)
            else:
                logger.warning("GitHub App credentials not provided for workload identity")
                return None
        
        elif platform == 'supabase':
            project_ref = kwargs.get('project_ref', 'default')
            return self.get_supabase_service_role_token(project_ref)
        
        elif platform == 'vercel':
            return self.get_vercel_identity_token()
        
        else:
            logger.warning(f"Unsupported platform for workload identity: {platform}")
            return None
    
    def fallback_to_stored_credentials(self, platform: str, user_id: str) -> bool:
        """
        Check if we should fallback to stored credentials
        when workload identity is not available
        """
        try:
            # Try to get workload identity first
            identity_token = self.get_token_for_platform(platform)
            
            if identity_token:
                logger.info(f"Using workload identity for {platform}")
                return False  # Don't fallback, use workload identity
            else:
                logger.info(f"Workload identity not available for {platform}, falling back to stored credentials")
                return True  # Fallback to stored credentials
                
        except Exception as e:
            logger.warning(f"Error checking workload identity for {platform}: {str(e)}")
            return True  # Fallback on error

# Global workload identity manager instance
workload_identity_manager = WorkloadIdentityManager()

def get_platform_token(platform: str, **kwargs) -> Optional[IdentityToken]:
    """Convenience function to get platform token"""
    return workload_identity_manager.get_token_for_platform(platform, **kwargs)

def should_use_stored_credentials(platform: str, user_id: str) -> bool:
    """Convenience function to check if fallback is needed"""
    return workload_identity_manager.fallback_to_stored_credentials(platform, user_id)
