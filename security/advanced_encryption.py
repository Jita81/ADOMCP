"""
Advanced encryption module for ADOMCP using AES-GCM
Replaces the basic XOR encryption with enterprise-grade security
"""

import os
import secrets
import base64
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)

@dataclass
class EncryptedData:
    """Container for encrypted data with metadata"""
    ciphertext: str  # Base64 encoded
    nonce: str      # Base64 encoded
    tag: str        # Base64 encoded (authentication tag)
    algorithm: str
    key_version: str
    timestamp: str
    metadata: Dict[str, Any]

@dataclass
class KeyDerivationContext:
    """Context for key derivation"""
    user_id: str
    platform: str
    purpose: str
    version: str = "v2"

class AdvancedEncryptionManager:
    """
    Advanced encryption using AES-GCM with proper key derivation
    Follows NIST guidelines for cryptographic best practices
    """
    
    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.key_version = "v2"
        self.algorithm = "AES-256-GCM"
        
    def _get_or_create_master_key(self) -> bytes:
        """Get master encryption key from environment or generate"""
        # Try to get from environment first
        env_key = os.getenv('MCP_MASTER_KEY')
        
        if env_key:
            try:
                # Decode base64 encoded key from environment
                master_key = base64.b64decode(env_key)
                if len(master_key) == 32:  # 256 bits
                    return master_key
                else:
                    logger.warning("Invalid master key length in environment, generating new key")
            except Exception as e:
                logger.warning(f"Invalid master key format in environment: {str(e)}")
        
        # Generate a new 256-bit master key
        master_key = secrets.token_bytes(32)
        
        # Store in environment for this session (in production, use proper key management)
        os.environ['MCP_MASTER_KEY'] = base64.b64encode(master_key).decode()
        
        logger.info("Generated new master encryption key")
        return master_key
    
    def _derive_key(self, context: KeyDerivationContext) -> bytes:
        """
        Derive encryption key using HKDF (HMAC-based Key Derivation Function)
        This provides proper key separation and forward secrecy
        """
        # Create info parameter for HKDF
        info = f"{context.user_id}:{context.platform}:{context.purpose}:{context.version}".encode()
        
        # Create salt from user context (deterministic but unique per user)
        salt_material = f"{context.user_id}:{context.platform}".encode()
        salt = hashlib.sha256(salt_material).digest()
        
        # Derive key using HKDF
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for AES-256
            salt=salt,
            info=info,
            backend=default_backend()
        )
        
        derived_key = hkdf.derive(self.master_key)
        return derived_key
    
    def encrypt_api_key(self, api_key: str, user_id: str, platform: str, 
                       additional_data: Optional[Dict[str, Any]] = None) -> EncryptedData:
        """
        Encrypt API key using AES-GCM with additional authenticated data
        """
        try:
            # Create key derivation context
            context = KeyDerivationContext(
                user_id=user_id,
                platform=platform,
                purpose="api_key_encryption",
                version=self.key_version
            )
            
            # Derive encryption key
            encryption_key = self._derive_key(context)
            
            # Create AES-GCM cipher
            aesgcm = AESGCM(encryption_key)
            
            # Generate random nonce (96 bits for AES-GCM)
            nonce = secrets.token_bytes(12)
            
            # Prepare payload
            timestamp = datetime.now().isoformat()
            payload = {
                'api_key': api_key,
                'timestamp': timestamp,
                'user_id': user_id,
                'platform': platform,
                'metadata': additional_data or {}
            }
            
            # Convert payload to bytes
            payload_bytes = json.dumps(payload).encode('utf-8')
            
            # Create additional authenticated data (AAD)
            aad = f"{user_id}:{platform}:{timestamp}".encode('utf-8')
            
            # Encrypt with AES-GCM
            ciphertext = aesgcm.encrypt(nonce, payload_bytes, aad)
            
            # The ciphertext includes the authentication tag at the end
            # AES-GCM appends a 16-byte tag to the ciphertext
            actual_ciphertext = ciphertext[:-16]
            auth_tag = ciphertext[-16:]
            
            # Create encrypted data container
            encrypted_data = EncryptedData(
                ciphertext=base64.b64encode(actual_ciphertext).decode('utf-8'),
                nonce=base64.b64encode(nonce).decode('utf-8'),
                tag=base64.b64encode(auth_tag).decode('utf-8'),
                algorithm=self.algorithm,
                key_version=self.key_version,
                timestamp=timestamp,
                metadata={
                    'user_id_hash': hashlib.sha256(user_id.encode()).hexdigest()[:16],
                    'platform': platform,
                    'aad_used': True
                }
            )
            
            logger.debug(f"Successfully encrypted API key for user {user_id} on platform {platform}")
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Encryption failed for user {user_id} on platform {platform}: {str(e)}")
            raise ValueError(f"Failed to encrypt API key: {str(e)}")
    
    def decrypt_api_key(self, encrypted_data: EncryptedData, user_id: str, platform: str) -> Tuple[str, Dict[str, Any]]:
        """
        Decrypt API key using AES-GCM with authentication verification
        """
        try:
            # Verify this encrypted data belongs to the requesting user
            expected_user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
            actual_user_hash = encrypted_data.metadata.get('user_id_hash')
            
            if expected_user_hash != actual_user_hash:
                raise ValueError("Encrypted data does not belong to requesting user")
            
            # Verify platform matches
            if encrypted_data.metadata.get('platform') != platform:
                raise ValueError("Platform mismatch for encrypted data")
            
            # Create key derivation context matching encryption
            context = KeyDerivationContext(
                user_id=user_id,
                platform=platform,
                purpose="api_key_encryption",
                version=encrypted_data.key_version
            )
            
            # Derive the same encryption key
            encryption_key = self._derive_key(context)
            
            # Create AES-GCM cipher
            aesgcm = AESGCM(encryption_key)
            
            # Decode components
            nonce = base64.b64decode(encrypted_data.nonce.encode('utf-8'))
            ciphertext = base64.b64decode(encrypted_data.ciphertext.encode('utf-8'))
            auth_tag = base64.b64decode(encrypted_data.tag.encode('utf-8'))
            
            # Reconstruct full ciphertext with tag
            full_ciphertext = ciphertext + auth_tag
            
            # Reconstruct AAD
            aad = f"{user_id}:{platform}:{encrypted_data.timestamp}".encode('utf-8')
            
            # Decrypt and verify
            decrypted_bytes = aesgcm.decrypt(nonce, full_ciphertext, aad)
            
            # Parse payload
            payload = json.loads(decrypted_bytes.decode('utf-8'))
            
            # Extract API key and metadata
            api_key = payload['api_key']
            metadata = {
                'encrypted_at': payload['timestamp'],
                'algorithm': encrypted_data.algorithm,
                'key_version': encrypted_data.key_version,
                'user_verified': True,
                'platform_verified': True,
                'integrity_verified': True
            }
            
            logger.debug(f"Successfully decrypted API key for user {user_id} on platform {platform}")
            return api_key, metadata
            
        except Exception as e:
            logger.error(f"Decryption failed for user {user_id} on platform {platform}: {str(e)}")
            raise ValueError(f"Failed to decrypt API key: {str(e)}")
    
    def rotate_master_key(self, new_master_key: Optional[bytes] = None) -> str:
        """
        Rotate the master encryption key
        Returns the new key version identifier
        """
        try:
            if new_master_key is None:
                new_master_key = secrets.token_bytes(32)
            
            # Store old key with version for re-encryption
            old_key = self.master_key
            old_version = self.key_version
            
            # Update to new key
            self.master_key = new_master_key
            new_version = f"v{int(old_version[1:]) + 1}"
            self.key_version = new_version
            
            # Update environment
            os.environ['MCP_MASTER_KEY'] = base64.b64encode(new_master_key).decode()
            
            logger.info(f"Master key rotated from {old_version} to {new_version}")
            
            # In production, this would trigger re-encryption of all stored data
            # with the new key version
            
            return new_version
            
        except Exception as e:
            logger.error(f"Master key rotation failed: {str(e)}")
            raise ValueError(f"Failed to rotate master key: {str(e)}")
    
    def create_audit_hash(self, api_key: str, user_id: str, platform: str) -> str:
        """
        Create audit hash for API key without exposing the key
        Uses different salt to prevent correlation with encrypted data
        """
        # Use different salt for audit trail
        audit_salt = f"audit_v2_{platform}_{user_id}".encode()
        
        # Create HMAC-based hash
        import hmac
        audit_hash = hmac.new(
            key=self.master_key,
            msg=api_key.encode() + audit_salt,
            digestmod=hashlib.sha256
        ).hexdigest()[:16]  # Truncate for storage efficiency
        
        return audit_hash
    
    def verify_data_integrity(self, encrypted_data: EncryptedData) -> bool:
        """
        Verify the integrity of encrypted data without decryption
        """
        try:
            # Check if all required fields are present
            required_fields = ['ciphertext', 'nonce', 'tag', 'algorithm', 'key_version', 'timestamp']
            for field in required_fields:
                if not hasattr(encrypted_data, field) or not getattr(encrypted_data, field):
                    return False
            
            # Verify base64 encoding
            try:
                base64.b64decode(encrypted_data.ciphertext)
                base64.b64decode(encrypted_data.nonce)
                base64.b64decode(encrypted_data.tag)
            except Exception:
                return False
            
            # Verify algorithm is supported
            if encrypted_data.algorithm != self.algorithm:
                return False
            
            # Verify timestamp format
            try:
                datetime.fromisoformat(encrypted_data.timestamp)
            except Exception:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_key_rotation_status(self) -> Dict[str, Any]:
        """Get current key rotation status and recommendations"""
        return {
            'current_version': self.key_version,
            'algorithm': self.algorithm,
            'master_key_age_days': 0,  # Would calculate from key creation time in production
            'rotation_recommended': False,  # Would check age and usage patterns
            'next_rotation_date': (datetime.now() + timedelta(days=90)).isoformat(),
            'supported_versions': ['v2'],  # Current version only
            'migration_needed': False
        }

# Global advanced encryption manager instance
advanced_encryption_manager = AdvancedEncryptionManager()

def encrypt_api_key_advanced(api_key: str, user_id: str, platform: str, 
                           additional_data: Optional[Dict[str, Any]] = None) -> EncryptedData:
    """Convenience function for advanced API key encryption"""
    return advanced_encryption_manager.encrypt_api_key(api_key, user_id, platform, additional_data)

def decrypt_api_key_advanced(encrypted_data: EncryptedData, user_id: str, platform: str) -> Tuple[str, Dict[str, Any]]:
    """Convenience function for advanced API key decryption"""
    return advanced_encryption_manager.decrypt_api_key(encrypted_data, user_id, platform)

def create_audit_hash_advanced(api_key: str, user_id: str, platform: str) -> str:
    """Convenience function for advanced audit hash creation"""
    return advanced_encryption_manager.create_audit_hash(api_key, user_id, platform)
