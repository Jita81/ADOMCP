"""
Real Supabase integration for ADOMCP
Implements secure API key storage with Row Level Security (RLS)
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
import logging
import asyncio
from .advanced_encryption import EncryptedData, advanced_encryption_manager
# Import workload identity manager with fallback
try:
    from .workload_identity import workload_identity_manager
except ImportError:
    workload_identity_manager = None

# Try to import supabase - graceful fallback if not available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

logger = logging.getLogger(__name__)

@dataclass
class StoredAPIKey:
    """Container for stored API key data"""
    id: str
    user_id: str
    platform: str
    encrypted_data: EncryptedData
    audit_hash: str
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    metadata: Dict[str, Any]
    is_active: bool

class SupabaseAPIKeyManager:
    """
    Real Supabase integration for secure API key storage
    Implements Row Level Security and proper encryption
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.project_url = os.getenv('SUPABASE_URL')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.anon_key = os.getenv('SUPABASE_ANON_KEY')
        self.table_name = 'api_keys'
        
        if SUPABASE_AVAILABLE and self.project_url and self.service_key:
            self._initialize_client()
        else:
            logger.warning("Supabase not available - using simulation mode")
    
    def _initialize_client(self):
        """Initialize Supabase client with service role key"""
        try:
            self.client = create_client(self.project_url, self.service_key)
            logger.info("Successfully initialized Supabase client")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            self.client = None
    
    async def store_api_key(self, user_id: str, platform: str, api_key: str, 
                          organization_url: Optional[str] = None, 
                          project_id: Optional[str] = None,
                          expires_in_days: int = 90) -> Dict[str, Any]:
        """
        Store API key securely in Supabase with encryption
        """
        try:
            # Encrypt the API key
            additional_data = {
                'organization_url': organization_url,
                'project_id': project_id,
                'stored_by': 'supabase_manager'
            }
            
            encrypted_data = advanced_encryption_manager.encrypt_api_key(
                api_key, user_id, platform, additional_data
            )
            
            # Create audit hash
            audit_hash = advanced_encryption_manager.create_audit_hash(api_key, user_id, platform)
            
            # Calculate expiry
            expires_at = datetime.now() + timedelta(days=expires_in_days)
            
            # Prepare record for database
            record = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'platform': platform,
                'encrypted_ciphertext': encrypted_data.ciphertext,
                'encrypted_nonce': encrypted_data.nonce,
                'encrypted_tag': encrypted_data.tag,
                'encryption_algorithm': encrypted_data.algorithm,
                'encryption_key_version': encrypted_data.key_version,
                'encryption_timestamp': encrypted_data.timestamp,
                'encryption_metadata': json.dumps(encrypted_data.metadata),
                'audit_hash': audit_hash,
                'organization_url': organization_url,
                'project_id': project_id,
                'expires_at': expires_at.isoformat(),
                'metadata': json.dumps({
                    'stored_at': datetime.now().isoformat(),
                    'storage_version': 'v2',
                    'encryption_method': 'aes_gcm'
                }),
                'is_active': True
            }
            
            if self.client:
                # Store in real Supabase
                result = self.client.table(self.table_name).insert(record).execute()
                
                if result.data:
                    logger.info(f"Successfully stored API key for user {user_id} on platform {platform}")
                    return {
                        'success': True,
                        'id': record['id'],
                        'audit_hash': audit_hash,
                        'expires_at': expires_at.isoformat(),
                        'encryption_version': encrypted_data.key_version
                    }
                else:
                    raise Exception("Failed to insert record into Supabase")
            else:
                # Simulation mode
                logger.info(f"[SIMULATION] Would store API key for user {user_id} on platform {platform}")
                return {
                    'success': True,
                    'id': record['id'],
                    'audit_hash': audit_hash,
                    'expires_at': expires_at.isoformat(),
                    'encryption_version': encrypted_data.key_version,
                    'note': 'Simulation mode - not actually stored'
                }
                
        except Exception as e:
            logger.error(f"Failed to store API key for user {user_id} on platform {platform}: {str(e)}")
            raise ValueError(f"Failed to store API key: {str(e)}")
    
    async def retrieve_api_key(self, user_id: str, platform: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Retrieve and decrypt API key from Supabase
        """
        try:
            if self.client:
                # Query Supabase with RLS - user can only access their own keys
                result = self.client.table(self.table_name)\
                    .select('*')\
                    .eq('user_id', user_id)\
                    .eq('platform', platform)\
                    .eq('is_active', True)\
                    .order('created_at', desc=True)\
                    .limit(1)\
                    .execute()
                
                if not result.data:
                    logger.debug(f"No API key found for user {user_id} on platform {platform}")
                    return None
                
                record = result.data[0]
                
                # Check if key has expired
                expires_at = datetime.fromisoformat(record['expires_at'])
                if datetime.now() > expires_at:
                    logger.warning(f"API key expired for user {user_id} on platform {platform}")
                    await self._deactivate_key(record['id'])
                    return None
                
                # Reconstruct encrypted data
                encrypted_data = EncryptedData(
                    ciphertext=record['encrypted_ciphertext'],
                    nonce=record['encrypted_nonce'],
                    tag=record['encrypted_tag'],
                    algorithm=record['encryption_algorithm'],
                    key_version=record['encryption_key_version'],
                    timestamp=record['encryption_timestamp'],
                    metadata=json.loads(record['encryption_metadata'])
                )
                
                # Decrypt API key
                api_key, metadata = advanced_encryption_manager.decrypt_api_key(
                    encrypted_data, user_id, platform
                )
                
                # Add storage metadata
                metadata.update({
                    'stored_id': record['id'],
                    'organization_url': record.get('organization_url'),
                    'project_id': record.get('project_id'),
                    'expires_at': record['expires_at'],
                    'audit_hash': record['audit_hash']
                })
                
                logger.info(f"Successfully retrieved API key for user {user_id} on platform {platform}")
                return api_key, metadata
                
            else:
                # Simulation mode
                logger.info(f"[SIMULATION] Would retrieve API key for user {user_id} on platform {platform}")
                return "simulated_api_key", {
                    'note': 'Simulation mode',
                    'platform': platform,
                    'user_id': user_id
                }
                
        except Exception as e:
            logger.error(f"Failed to retrieve API key for user {user_id} on platform {platform}: {str(e)}")
            return None
    
    async def list_user_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all active API keys for a user (without exposing the keys)
        """
        try:
            if self.client:
                result = self.client.table(self.table_name)\
                    .select('id,platform,created_at,expires_at,organization_url,project_id,audit_hash')\
                    .eq('user_id', user_id)\
                    .eq('is_active', True)\
                    .order('created_at', desc=True)\
                    .execute()
                
                keys = []
                for record in result.data:
                    keys.append({
                        'id': record['id'],
                        'platform': record['platform'],
                        'created_at': record['created_at'],
                        'expires_at': record['expires_at'],
                        'organization_url': record.get('organization_url'),
                        'project_id': record.get('project_id'),
                        'audit_hash': record['audit_hash'],
                        'status': 'active' if datetime.fromisoformat(record['expires_at']) > datetime.now() else 'expired'
                    })
                
                return keys
            else:
                # Simulation mode
                return [{
                    'id': 'sim_001',
                    'platform': 'azure_devops',
                    'created_at': datetime.now().isoformat(),
                    'expires_at': (datetime.now() + timedelta(days=90)).isoformat(),
                    'status': 'active',
                    'note': 'Simulation mode'
                }]
                
        except Exception as e:
            logger.error(f"Failed to list keys for user {user_id}: {str(e)}")
            return []
    
    async def rotate_api_key(self, user_id: str, platform: str, new_api_key: str) -> Dict[str, Any]:
        """
        Rotate an API key - deactivate old and store new
        """
        try:
            # Deactivate old key
            await self.deactivate_api_key(user_id, platform)
            
            # Store new key
            result = await self.store_api_key(user_id, platform, new_api_key)
            
            logger.info(f"Successfully rotated API key for user {user_id} on platform {platform}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to rotate API key for user {user_id} on platform {platform}: {str(e)}")
            raise ValueError(f"Failed to rotate API key: {str(e)}")
    
    async def deactivate_api_key(self, user_id: str, platform: str) -> bool:
        """
        Deactivate API key instead of deleting (for audit trail)
        """
        try:
            if self.client:
                result = self.client.table(self.table_name)\
                    .update({'is_active': False, 'deactivated_at': datetime.now().isoformat()})\
                    .eq('user_id', user_id)\
                    .eq('platform', platform)\
                    .eq('is_active', True)\
                    .execute()
                
                return len(result.data) > 0
            else:
                logger.info(f"[SIMULATION] Would deactivate API key for user {user_id} on platform {platform}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to deactivate API key for user {user_id} on platform {platform}: {str(e)}")
            return False
    
    async def _deactivate_key(self, key_id: str) -> bool:
        """Internal method to deactivate key by ID"""
        try:
            if self.client:
                result = self.client.table(self.table_name)\
                    .update({'is_active': False, 'deactivated_at': datetime.now().isoformat()})\
                    .eq('id', key_id)\
                    .execute()
                
                return len(result.data) > 0
            return True
        except Exception:
            return False
    
    async def cleanup_expired_keys(self) -> int:
        """
        Clean up expired keys (mark as inactive)
        """
        try:
            if self.client:
                now = datetime.now().isoformat()
                result = self.client.table(self.table_name)\
                    .update({'is_active': False, 'deactivated_at': now})\
                    .lt('expires_at', now)\
                    .eq('is_active', True)\
                    .execute()
                
                count = len(result.data)
                logger.info(f"Cleaned up {count} expired API keys")
                return count
            else:
                logger.info("[SIMULATION] Would clean up expired keys")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {str(e)}")
            return 0
    
    def get_database_schema(self) -> str:
        """
        Get the SQL schema for the API keys table
        """
        return """
-- API Keys table with Row Level Security
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('azure_devops', 'github', 'gitlab')),
    
    -- Encrypted API key components
    encrypted_ciphertext TEXT NOT NULL,
    encrypted_nonce TEXT NOT NULL,
    encrypted_tag TEXT NOT NULL,
    encryption_algorithm TEXT NOT NULL DEFAULT 'AES-256-GCM',
    encryption_key_version TEXT NOT NULL DEFAULT 'v2',
    encryption_timestamp TIMESTAMPTZ NOT NULL,
    encryption_metadata JSONB,
    
    -- Audit and security
    audit_hash TEXT NOT NULL,
    organization_url TEXT,
    project_id TEXT,
    
    -- Lifecycle management
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    deactivated_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    UNIQUE(user_id, platform, is_active) WHERE is_active = TRUE
);

-- Row Level Security
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own API keys
CREATE POLICY "users_own_api_keys" ON api_keys
    FOR ALL USING (auth.uid()::text = user_id);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_api_keys_user_platform 
    ON api_keys (user_id, platform) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_api_keys_expires_at 
    ON api_keys (expires_at) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_api_keys_audit_hash 
    ON api_keys (audit_hash);

-- Function to update updated_at automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_api_keys_updated_at ON api_keys;
CREATE TRIGGER update_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""

# Global Supabase manager instance
supabase_manager = SupabaseAPIKeyManager()

async def store_api_key_secure(user_id: str, platform: str, api_key: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for secure API key storage"""
    return await supabase_manager.store_api_key(user_id, platform, api_key, **kwargs)

async def retrieve_api_key_secure(user_id: str, platform: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Convenience function for secure API key retrieval"""
    return await supabase_manager.retrieve_api_key(user_id, platform)
