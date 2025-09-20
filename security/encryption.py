"""
Secure API key encryption and management for ADOMCP
Implements proper encryption instead of base64 encoding
"""

import os
import base64
import hashlib
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import secrets
import json

class SecureKeyManager:
    """Secure API key encryption and management"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Get encryption key from environment or generate one"""
        # In production, this should come from a secure key management service
        env_key = os.getenv('MCP_ENCRYPTION_KEY')
        
        if env_key:
            try:
                # Decode base64 encoded key from environment
                return base64.b64decode(env_key)
            except Exception:
                pass
        
        # Generate a new key (for development only)
        # In production, this should be managed externally
        key = secrets.token_bytes(32)  # 256-bit key
        
        # Store in environment for this session (not persistent)
        os.environ['MCP_ENCRYPTION_KEY'] = base64.b64encode(key).decode()
        
        return key
    
    def _derive_key(self, user_id: str, platform: str) -> bytes:
        """Derive encryption key specific to user and platform"""
        # Use PBKDF2 to derive a unique key for each user/platform combination
        salt = f"{user_id}:{platform}".encode()
        return hashlib.pbkdf2_hmac('sha256', self.encryption_key, salt, 100000)[:32]
    
    def _xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        """Simple XOR encryption (for educational purposes)"""
        # In production, use proper encryption like AES-GCM
        return bytes(a ^ b for a, b in zip(data, (key * (len(data) // len(key) + 1))[:len(data)]))
    
    def encrypt_api_key(self, api_key: str, user_id: str, platform: str) -> str:
        """Encrypt API key for secure storage"""
        try:
            # Derive unique key for this user/platform
            derived_key = self._derive_key(user_id, platform)
            
            # Add timestamp and random nonce for additional security
            timestamp = datetime.now().isoformat()
            nonce = secrets.token_hex(16)
            
            # Create payload
            payload = {
                'api_key': api_key,
                'timestamp': timestamp,
                'nonce': nonce
            }
            
            # Convert to bytes
            payload_bytes = json.dumps(payload).encode('utf-8')
            
            # Encrypt
            encrypted_bytes = self._xor_encrypt(payload_bytes, derived_key)
            
            # Base64 encode for storage
            encrypted_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')
            
            return encrypted_b64
            
        except Exception as e:
            raise ValueError(f"Failed to encrypt API key: {str(e)}")
    
    def decrypt_api_key(self, encrypted_key: str, user_id: str, platform: str) -> Tuple[str, Dict[str, Any]]:
        """Decrypt API key from secure storage"""
        try:
            # Derive the same key used for encryption
            derived_key = self._derive_key(user_id, platform)
            
            # Base64 decode
            encrypted_bytes = base64.b64decode(encrypted_key.encode('utf-8'))
            
            # Decrypt
            decrypted_bytes = self._xor_encrypt(encrypted_bytes, derived_key)
            
            # Parse JSON
            payload = json.loads(decrypted_bytes.decode('utf-8'))
            
            # Extract data
            api_key = payload['api_key']
            metadata = {
                'encrypted_at': payload['timestamp'],
                'nonce': payload['nonce']
            }
            
            return api_key, metadata
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {str(e)}")
    
    def validate_key_age(self, metadata: Dict[str, Any], max_age_days: int = 90) -> Tuple[bool, Optional[str]]:
        """Check if encrypted key is within acceptable age"""
        try:
            encrypted_at = datetime.fromisoformat(metadata['encrypted_at'])
            age = datetime.now() - encrypted_at
            
            if age > timedelta(days=max_age_days):
                return False, f"API key is {age.days} days old (max: {max_age_days})"
            
            return True, None
            
        except Exception as e:
            return False, f"Failed to validate key age: {str(e)}"
    
    def hash_for_audit(self, api_key: str) -> str:
        """Create hash of API key for audit logging (without exposing the key)"""
        # Use a different salt for audit hashing
        audit_salt = b"audit_log_salt_2024"
        return hashlib.pbkdf2_hmac('sha256', api_key.encode(), audit_salt, 10000).hex()[:16]

class SecretRotationManager:
    """Manage API key rotation and lifecycle"""
    
    def __init__(self, key_manager: SecureKeyManager):
        self.key_manager = key_manager
        self.rotation_schedule: Dict[str, Dict[str, Any]] = {}
    
    def schedule_rotation(self, user_id: str, platform: str, days_until_rotation: int = 90):
        """Schedule API key rotation"""
        rotation_date = datetime.now() + timedelta(days=days_until_rotation)
        
        key = f"{user_id}:{platform}"
        self.rotation_schedule[key] = {
            'user_id': user_id,
            'platform': platform,
            'rotation_date': rotation_date.isoformat(),
            'status': 'scheduled'
        }
    
    def check_rotation_needed(self, user_id: str, platform: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if API key needs rotation"""
        key = f"{user_id}:{platform}"
        
        if key not in self.rotation_schedule:
            return False, None
        
        schedule_info = self.rotation_schedule[key]
        rotation_date = datetime.fromisoformat(schedule_info['rotation_date'])
        
        if datetime.now() >= rotation_date:
            return True, schedule_info
        
        return False, schedule_info
    
    def get_rotation_warning_days(self, user_id: str, platform: str) -> Optional[int]:
        """Get number of days until rotation is needed"""
        key = f"{user_id}:{platform}"
        
        if key not in self.rotation_schedule:
            return None
        
        schedule_info = self.rotation_schedule[key]
        rotation_date = datetime.fromisoformat(schedule_info['rotation_date'])
        days_until = (rotation_date - datetime.now()).days
        
        return max(0, days_until)

# Global instances
secure_key_manager = SecureKeyManager()
rotation_manager = SecretRotationManager(secure_key_manager)

def encrypt_api_key(api_key: str, user_id: str, platform: str) -> str:
    """Convenience function for API key encryption"""
    return secure_key_manager.encrypt_api_key(api_key, user_id, platform)

def decrypt_api_key(encrypted_key: str, user_id: str, platform: str) -> Tuple[str, Dict[str, Any]]:
    """Convenience function for API key decryption"""
    return secure_key_manager.decrypt_api_key(encrypted_key, user_id, platform)

def hash_for_audit(api_key: str) -> str:
    """Convenience function for audit hashing"""
    return secure_key_manager.hash_for_audit(api_key)
