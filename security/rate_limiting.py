"""
Rate limiting and security protection for ADOMCP
Implements per-IP rate limiting, DDoS protection, and security headers
"""

import time
import hashlib
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json

class RateLimiter:
    """Advanced rate limiting with burst support and security features"""
    
    def __init__(self):
        # Storage for rate limiting data
        self.request_counts: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, float] = {}  # IP -> unblock_time
        self.suspicious_ips: Dict[str, int] = defaultdict(int)  # IP -> violation_count
        
        # Rate limiting configuration
        self.limits = {
            'general': {'requests': 60, 'window': 60},      # 60 requests per minute
            'auth': {'requests': 10, 'window': 60},         # 10 auth attempts per minute
            'create': {'requests': 30, 'window': 60},       # 30 create operations per minute
            'heavy': {'requests': 5, 'window': 60}          # 5 heavy operations per minute
        }
        
        # Security thresholds
        self.security_config = {
            'max_violations': 5,          # Max violations before blocking
            'block_duration': 300,        # Block for 5 minutes
            'cleanup_interval': 3600,     # Clean old data every hour
            'max_request_size': 1024 * 1024,  # 1MB max request
            'suspicious_threshold': 3      # Violations before marking suspicious
        }
        
        self.last_cleanup = time.time()
    
    def _cleanup_old_data(self):
        """Clean up old rate limiting data"""
        current_time = time.time()
        
        if current_time - self.last_cleanup < self.security_config['cleanup_interval']:
            return
        
        # Clean up request counts older than max window
        max_window = max(limit['window'] for limit in self.limits.values())
        cutoff_time = current_time - max_window
        
        for ip in list(self.request_counts.keys()):
            requests = self.request_counts[ip]
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            
            if not requests:
                del self.request_counts[ip]
        
        # Clean up expired blocks
        expired_blocks = [
            ip for ip, unblock_time in self.blocked_ips.items()
            if current_time > unblock_time
        ]
        for ip in expired_blocks:
            del self.blocked_ips[ip]
            if ip in self.suspicious_ips:
                self.suspicious_ips[ip] = max(0, self.suspicious_ips[ip] - 1)
        
        self.last_cleanup = current_time
    
    def _get_client_identifier(self, client_ip: str, user_agent: str = "") -> str:
        """Create unique client identifier"""
        # Combine IP and hashed user agent for better identification
        ua_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8] if user_agent else "unknown"
        return f"{client_ip}:{ua_hash}"
    
    def _is_blocked(self, client_id: str) -> Tuple[bool, Optional[float]]:
        """Check if client is currently blocked"""
        client_ip = client_id.split(':')[0]
        current_time = time.time()
        
        if client_ip in self.blocked_ips:
            unblock_time = self.blocked_ips[client_ip]
            if current_time < unblock_time:
                return True, unblock_time - current_time
            else:
                del self.blocked_ips[client_ip]
        
        return False, None
    
    def _block_client(self, client_id: str, duration: Optional[int] = None):
        """Block client for specified duration"""
        client_ip = client_id.split(':')[0]
        duration = duration or self.security_config['block_duration']
        unblock_time = time.time() + duration
        
        self.blocked_ips[client_ip] = unblock_time
        self.suspicious_ips[client_ip] += 1
    
    def _check_rate_limit(self, client_id: str, limit_type: str = 'general') -> Tuple[bool, Dict[str, any]]:
        """Check if request is within rate limits"""
        current_time = time.time()
        limit_config = self.limits.get(limit_type, self.limits['general'])
        
        window = limit_config['window']
        max_requests = limit_config['requests']
        cutoff_time = current_time - window
        
        # Get and clean old requests for this client
        requests = self.request_counts[client_id]
        while requests and requests[0] < cutoff_time:
            requests.popleft()
        
        # Check if limit exceeded
        if len(requests) >= max_requests:
            violation_info = {
                'limit_type': limit_type,
                'current_count': len(requests),
                'max_allowed': max_requests,
                'window_seconds': window,
                'retry_after': int(requests[0] + window - current_time) + 1
            }
            return False, violation_info
        
        # Add current request
        requests.append(current_time)
        
        return True, {
            'limit_type': limit_type,
            'current_count': len(requests),
            'max_allowed': max_requests,
            'remaining': max_requests - len(requests)
        }
    
    def check_request(self, client_ip: str, endpoint: str, user_agent: str = "", 
                     request_size: int = 0) -> Tuple[bool, Dict[str, any]]:
        """Main rate limiting check for incoming requests"""
        
        self._cleanup_old_data()
        
        client_id = self._get_client_identifier(client_ip, user_agent)
        
        # Check if client is blocked
        is_blocked, remaining_block_time = self._is_blocked(client_id)
        if is_blocked:
            return False, {
                'error': 'rate_limit_blocked',
                'message': 'Client is temporarily blocked due to rate limit violations',
                'retry_after': int(remaining_block_time) + 1,
                'block_reason': 'excessive_requests'
            }
        
        # Check request size
        if request_size > self.security_config['max_request_size']:
            self._block_client(client_id, 60)  # Block for 1 minute for oversized requests
            return False, {
                'error': 'request_too_large',
                'message': 'Request size exceeds maximum allowed',
                'max_size': self.security_config['max_request_size']
            }
        
        # Determine rate limit type based on endpoint
        limit_type = 'general'
        if '/auth' in endpoint or '/keys' in endpoint:
            limit_type = 'auth'
        elif any(action in endpoint for action in ['/create', '/upload']):
            limit_type = 'create'
        elif any(action in endpoint for action in ['/bulk', '/batch']):
            limit_type = 'heavy'
        
        # Check rate limits
        allowed, rate_info = self._check_rate_limit(client_id, limit_type)
        
        if not allowed:
            # Handle rate limit violation
            violations = self.suspicious_ips[client_ip] + 1
            
            if violations >= self.security_config['max_violations']:
                # Block client after multiple violations
                self._block_client(client_id)
                rate_info.update({
                    'error': 'rate_limit_blocked',
                    'message': 'Client blocked due to repeated rate limit violations',
                    'block_duration': self.security_config['block_duration']
                })
            else:
                rate_info.update({
                    'error': 'rate_limit_exceeded',
                    'message': f'Rate limit exceeded for {limit_type} operations',
                    'violations': violations,
                    'max_violations': self.security_config['max_violations']
                })
            
            return False, rate_info
        
        return True, rate_info
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers to add to responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'none'; object-src 'none';",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
    
    def get_cors_headers(self, origin: str = "*") -> Dict[str, str]:
        """Get CORS headers (restrictive by default)"""
        # In production, replace "*" with specific allowed origins
        return {
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Correlation-ID',
            'Access-Control-Max-Age': '3600',
            'Access-Control-Allow-Credentials': 'false'
        }
    
    def log_security_event(self, client_ip: str, event_type: str, details: Dict[str, any]) -> Dict[str, any]:
        """Log security events for monitoring"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_ip,
            'event_type': event_type,
            'details': details,
            'client_status': {
                'is_suspicious': self.suspicious_ips.get(client_ip, 0) >= self.security_config['suspicious_threshold'],
                'violation_count': self.suspicious_ips.get(client_ip, 0),
                'is_blocked': client_ip in self.blocked_ips
            }
        }
        
        # In production, this would go to a proper logging system
        # For now, we'll return it for the caller to handle
        return event

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(client_ip: str, endpoint: str, user_agent: str = "", 
                    request_size: int = 0) -> Tuple[bool, Dict[str, any]]:
    """Convenience function for rate limit checking"""
    return rate_limiter.check_request(client_ip, endpoint, user_agent, request_size)

def get_security_headers() -> Dict[str, str]:
    """Convenience function to get security headers"""
    return rate_limiter.get_security_headers()

def get_cors_headers(origin: str = "*") -> Dict[str, str]:
    """Convenience function to get CORS headers"""
    return rate_limiter.get_cors_headers(origin)
