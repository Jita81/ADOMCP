"""
Security module for ADOMCP
Provides validation, rate limiting, encryption, workload identity, and observability
"""

from .validation import SecurityValidator
from .rate_limiting import check_rate_limit, get_security_headers, get_cors_headers, rate_limiter
from .encryption import encrypt_api_key, decrypt_api_key, hash_for_audit, secure_key_manager, rotation_manager
from .advanced_encryption import (
    encrypt_api_key_advanced, decrypt_api_key_advanced, create_audit_hash_advanced,
    advanced_encryption_manager, EncryptedData
)
from .workload_identity import (
    get_platform_token, should_use_stored_credentials, workload_identity_manager, IdentityToken
)
from .observability import (
    start_request_trace, end_request_trace, observability_manager, trace_function
)
from .authentication import (
    authenticate_api_request, generate_user_api_key, validate_user_access, auth_manager
)

# Try to import Supabase integration
try:
    from .supabase_integration import (
        store_api_key_secure, retrieve_api_key_secure, supabase_manager
    )
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    store_api_key_secure = None
    retrieve_api_key_secure = None
    supabase_manager = None

__all__ = [
    # Basic security
    'SecurityValidator',
    'check_rate_limit',
    'get_security_headers', 
    'get_cors_headers',
    'rate_limiter',
    
    # Legacy encryption
    'encrypt_api_key',
    'decrypt_api_key',
    'hash_for_audit',
    'secure_key_manager',
    'rotation_manager',
    
    # Advanced encryption
    'encrypt_api_key_advanced',
    'decrypt_api_key_advanced',
    'create_audit_hash_advanced',
    'advanced_encryption_manager',
    'EncryptedData',
    
    # Workload identity
    'get_platform_token',
    'should_use_stored_credentials', 
    'workload_identity_manager',
    'IdentityToken',
    
    # Observability
    'start_request_trace',
    'end_request_trace',
    'observability_manager',
    'trace_function',
    
    # Authentication
    'authenticate_api_request',
    'generate_user_api_key',
    'validate_user_access',
    'auth_manager',
    
    # Supabase integration (if available)
    'store_api_key_secure',
    'retrieve_api_key_secure',
    'supabase_manager',
    'SUPABASE_AVAILABLE'
]
