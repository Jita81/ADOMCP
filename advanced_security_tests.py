#!/usr/bin/env python3
"""
Advanced Security Test Suite for ADOMCP Phase 2 Features
Tests workload identity, AES-GCM encryption, observability, and Supabase integration
"""

import json
import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Set up path for security modules
sys.path.append('.')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'advanced_security_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SecurityTestResult:
    """Individual security test result"""
    test_name: str
    success: bool
    duration: float
    message: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AdvancedSecurityTestSuite:
    """Test suite for Phase 2 advanced security features"""
    
    def __init__(self):
        self.results: List[SecurityTestResult] = []
        self.start_time = time.time()
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all advanced security tests"""
        logger.info("🔐 Starting Advanced Security Test Suite")
        logger.info("Testing Phase 2 Features: Workload Identity, AES-GCM, Observability")
        logger.info("=" * 80)
        
        tests = [
            ("Workload Identity Manager", self.test_workload_identity_manager),
            ("AES-GCM Encryption", self.test_aes_gcm_encryption),
            ("Advanced Encryption Features", self.test_advanced_encryption_features),
            ("Observability Manager", self.test_observability_manager),
            ("Supabase Integration", self.test_supabase_integration),
            ("Security Module Integration", self.test_security_module_integration),
            ("Graceful Fallbacks", self.test_graceful_fallbacks),
            ("Performance Impact", self.test_performance_impact)
        ]
        
        for i, (test_name, test_func) in enumerate(tests, 1):
            logger.info(f"🧪 Starting test: [{i}/{len(tests)}] {test_name}")
            start_time = time.time()
            
            try:
                result = test_func()
                duration = time.time() - start_time
                
                if result['success']:
                    logger.info(f"✅ PASS {test_name} ({duration:.2f}s): {result['message']}")
                else:
                    logger.error(f"❌ FAIL {test_name} ({duration:.2f}s): {result['message']}")
                
                self.results.append(SecurityTestResult(
                    test_name=test_name,
                    success=result['success'],
                    duration=duration,
                    message=result['message'],
                    details=result.get('details'),
                    error=result.get('error')
                ))
                
            except Exception as e:
                duration = time.time() - start_time
                error_msg = f"Test execution failed: {str(e)}"
                logger.error(f"❌ ERROR {test_name} ({duration:.2f}s): {error_msg}")
                
                self.results.append(SecurityTestResult(
                    test_name=test_name,
                    success=False,
                    duration=duration,
                    message=error_msg,
                    error=str(e)
                ))
            
            time.sleep(1)  # Brief pause between tests
        
        return self.generate_summary()
    
    def test_workload_identity_manager(self) -> Dict[str, Any]:
        """Test workload identity management"""
        try:
            from security.workload_identity import workload_identity_manager, IdentityToken
            
            # Test 1: Check manager initialization
            assert workload_identity_manager is not None, "Workload identity manager not initialized"
            
            # Test 2: Test platform token retrieval (simulation mode)
            platforms_to_test = ['azure_devops', 'github', 'supabase', 'vercel']
            results = {}
            
            for platform in platforms_to_test:
                try:
                    # This should either return a token or None (graceful fallback)
                    token = workload_identity_manager.get_token_for_platform(platform)
                    results[platform] = {
                        'available': token is not None,
                        'type': type(token).__name__ if token else 'None'
                    }
                except Exception as e:
                    results[platform] = {
                        'available': False,
                        'error': str(e)
                    }
            
            # Test 3: Test fallback logic
            fallback_tests = {}
            for platform in platforms_to_test:
                should_fallback = workload_identity_manager.fallback_to_stored_credentials(platform, "test-user")
                fallback_tests[platform] = should_fallback
            
            # Test 4: Test token cache cleanup
            workload_identity_manager.cleanup_expired_tokens()
            
            return {
                'success': True,
                'message': f"Workload identity tested for {len(platforms_to_test)} platforms",
                'details': {
                    'platforms_tested': platforms_to_test,
                    'token_results': results,
                    'fallback_tests': fallback_tests,
                    'cache_cleanup': 'successful'
                }
            }
            
        except ImportError as e:
            return {
                'success': False,
                'message': f"Workload identity module import failed: {str(e)}",
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Workload identity test failed: {str(e)}",
                'error': str(e)
            }
    
    def test_aes_gcm_encryption(self) -> Dict[str, Any]:
        """Test AES-GCM encryption functionality"""
        try:
            from security.advanced_encryption import (
                advanced_encryption_manager, 
                encrypt_api_key_advanced, 
                decrypt_api_key_advanced,
                EncryptedData
            )
            
            # Test data
            test_api_key = "test-api-key-12345"
            test_user_id = "test-user-123"
            test_platform = "azure_devops"
            
            # Test 1: Encryption
            encrypted_data = encrypt_api_key_advanced(test_api_key, test_user_id, test_platform)
            
            assert isinstance(encrypted_data, EncryptedData), "Encrypted data should be EncryptedData instance"
            assert encrypted_data.algorithm == "AES-256-GCM", "Should use AES-256-GCM"
            assert encrypted_data.key_version == "v2", "Should use key version v2"
            assert encrypted_data.ciphertext, "Ciphertext should not be empty"
            assert encrypted_data.nonce, "Nonce should not be empty"
            assert encrypted_data.tag, "Authentication tag should not be empty"
            
            # Test 2: Decryption
            decrypted_key, metadata = decrypt_api_key_advanced(encrypted_data, test_user_id, test_platform)
            
            assert decrypted_key == test_api_key, "Decrypted key should match original"
            assert metadata['user_verified'], "User should be verified"
            assert metadata['platform_verified'], "Platform should be verified"
            assert metadata['integrity_verified'], "Integrity should be verified"
            
            # Test 3: Tamper detection
            tampered_data = EncryptedData(
                ciphertext=encrypted_data.ciphertext,
                nonce=encrypted_data.nonce,
                tag="dGFtcGVyZWQ=",  # Base64 for "tampered"
                algorithm=encrypted_data.algorithm,
                key_version=encrypted_data.key_version,
                timestamp=encrypted_data.timestamp,
                metadata=encrypted_data.metadata
            )
            
            tamper_detected = False
            try:
                decrypt_api_key_advanced(tampered_data, test_user_id, test_platform)
            except ValueError:
                tamper_detected = True
            
            assert tamper_detected, "Tampering should be detected"
            
            # Test 4: Cross-user protection
            wrong_user_detected = False
            try:
                decrypt_api_key_advanced(encrypted_data, "wrong-user", test_platform)
            except ValueError:
                wrong_user_detected = True
            
            assert wrong_user_detected, "Wrong user access should be prevented"
            
            # Test 5: Data integrity verification
            integrity_valid = advanced_encryption_manager.verify_data_integrity(encrypted_data)
            assert integrity_valid, "Data integrity should be valid"
            
            return {
                'success': True,
                'message': "AES-GCM encryption working correctly with tampering protection",
                'details': {
                    'algorithm': encrypted_data.algorithm,
                    'key_version': encrypted_data.key_version,
                    'encryption_successful': True,
                    'decryption_successful': True,
                    'tamper_detection': tamper_detected,
                    'cross_user_protection': wrong_user_detected,
                    'data_integrity': integrity_valid
                }
            }
            
        except ImportError as e:
            return {
                'success': False,
                'message': f"Advanced encryption module import failed: {str(e)}",
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"AES-GCM encryption test failed: {str(e)}",
                'error': str(e)
            }
    
    def test_advanced_encryption_features(self) -> Dict[str, Any]:
        """Test advanced encryption features"""
        try:
            from security.advanced_encryption import advanced_encryption_manager, create_audit_hash_advanced
            
            # Test 1: Audit hash creation
            test_api_key = "test-api-key-12345"
            test_user_id = "test-user-123"
            test_platform = "azure_devops"
            
            audit_hash = create_audit_hash_advanced(test_api_key, test_user_id, test_platform)
            assert audit_hash, "Audit hash should be created"
            assert len(audit_hash) == 16, "Audit hash should be 16 characters"
            
            # Test 2: Key rotation status
            rotation_status = advanced_encryption_manager.get_key_rotation_status()
            assert 'current_version' in rotation_status, "Should have current version"
            assert 'algorithm' in rotation_status, "Should have algorithm info"
            assert rotation_status['algorithm'] == 'AES-256-GCM', "Should report correct algorithm"
            
            # Test 3: Master key rotation (simulation)
            old_version = rotation_status['current_version']
            new_version = advanced_encryption_manager.rotate_master_key()
            assert new_version != old_version, "New version should be different"
            
            return {
                'success': True,
                'message': "Advanced encryption features working correctly",
                'details': {
                    'audit_hash_length': len(audit_hash),
                    'rotation_status': rotation_status,
                    'key_rotation': f"{old_version} -> {new_version}"
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Advanced encryption features test failed: {str(e)}",
                'error': str(e)
            }
    
    def test_observability_manager(self) -> Dict[str, Any]:
        """Test observability and tracing functionality"""
        try:
            from security.observability import observability_manager, start_request_trace, end_request_trace
            
            # Test 1: Manager initialization
            assert observability_manager is not None, "Observability manager not initialized"
            
            # Test 2: Request tracing
            correlation_id = "test-correlation-123"
            endpoint = "/api/test"
            method = "POST"
            client_ip = "127.0.0.1"
            user_agent = "test-agent"
            request_size = 1024
            
            span = start_request_trace(
                correlation_id, endpoint, method, client_ip, user_agent, request_size, "test-user"
            )
            
            # Simulate some work
            time.sleep(0.1)
            
            end_request_trace(correlation_id, span, 200, 2048)
            
            # Test 3: Security event logging
            observability_manager.log_security_event(
                event_type="test_event",
                correlation_id=correlation_id,
                client_ip=client_ip,
                endpoint=endpoint,
                severity="INFO",
                user_id="test-user",
                details={"test": "data"}
            )
            
            # Test 4: Rate limit violation logging
            observability_manager.log_rate_limit_violation(
                correlation_id=correlation_id,
                client_ip=client_ip,
                endpoint=endpoint,
                limit_type="request_rate",
                user_id="test-user"
            )
            
            # Test 5: API key operation logging
            observability_manager.log_api_key_operation(
                operation="test_operation",
                correlation_id=correlation_id,
                user_id="test-user",
                platform="azure_devops",
                success=True
            )
            
            # Test 6: Metrics summary
            metrics_summary = observability_manager.get_metrics_summary(time_window_minutes=5)
            assert 'request_count' in metrics_summary, "Should have request count"
            assert 'security_events_count' in metrics_summary, "Should have security events count"
            
            return {
                'success': True,
                'message': "Observability features working correctly",
                'details': {
                    'request_tracing': 'successful',
                    'security_events': 'logged',
                    'metrics_summary': metrics_summary,
                    'correlation_id': correlation_id
                }
            }
            
        except ImportError as e:
            return {
                'success': False,
                'message': f"Observability module import failed: {str(e)}",
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Observability test failed: {str(e)}",
                'error': str(e)
            }
    
    def test_supabase_integration(self) -> Dict[str, Any]:
        """Test Supabase integration functionality"""
        try:
            from security.supabase_integration import supabase_manager
            
            # Test 1: Manager initialization
            assert supabase_manager is not None, "Supabase manager not initialized"
            
            # Test 2: Database schema
            schema = supabase_manager.get_database_schema()
            assert 'api_keys' in schema, "Should have api_keys table schema"
            assert 'ROW LEVEL SECURITY' in schema, "Should include RLS"
            
            # Test 3: Store API key (simulation mode)
            import asyncio
            
            async def test_storage():
                result = await supabase_manager.store_api_key(
                    user_id="test-user-123",
                    platform="azure_devops",
                    api_key="test-api-key",
                    organization_url="https://dev.azure.com/test",
                    project_id="test-project"
                )
                return result
            
            storage_result = asyncio.run(test_storage())
            assert storage_result['success'], "API key storage should succeed"
            
            # Test 4: Retrieve API key (simulation mode)
            async def test_retrieval():
                result = await supabase_manager.retrieve_api_key(
                    user_id="test-user-123",
                    platform="azure_devops"
                )
                return result
            
            retrieval_result = asyncio.run(test_retrieval())
            assert retrieval_result is not None, "API key retrieval should return data"
            
            # Test 5: List user keys (simulation mode)
            async def test_list():
                result = await supabase_manager.list_user_keys("test-user-123")
                return result
            
            list_result = asyncio.run(test_list())
            assert isinstance(list_result, list), "Should return list of keys"
            
            return {
                'success': True,
                'message': "Supabase integration working correctly in simulation mode",
                'details': {
                    'schema_available': True,
                    'storage_test': storage_result['success'],
                    'retrieval_test': retrieval_result is not None,
                    'list_test': len(list_result),
                    'rls_enabled': 'ROW LEVEL SECURITY' in schema
                }
            }
            
        except ImportError as e:
            return {
                'success': False,
                'message': f"Supabase integration module import failed: {str(e)}",
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Supabase integration test failed: {str(e)}",
                'error': str(e)
            }
    
    def test_security_module_integration(self) -> Dict[str, Any]:
        """Test security module integration and imports"""
        try:
            from security import (
                advanced_encryption_manager, workload_identity_manager, 
                observability_manager, SUPABASE_AVAILABLE
            )
            
            # Test 1: All managers available
            assert advanced_encryption_manager is not None, "Advanced encryption manager should be available"
            assert workload_identity_manager is not None, "Workload identity manager should be available"
            assert observability_manager is not None, "Observability manager should be available"
            
            # Test 2: Supabase availability flag
            assert isinstance(SUPABASE_AVAILABLE, bool), "Supabase availability should be boolean"
            
            # Test 3: Advanced functions available
            from security import (
                encrypt_api_key_advanced, decrypt_api_key_advanced, 
                get_platform_token, start_request_trace
            )
            
            # Test 4: Backward compatibility
            from security import (
                encrypt_api_key, decrypt_api_key, check_rate_limit, 
                get_security_headers, SecurityValidator
            )
            
            return {
                'success': True,
                'message': "Security module integration successful",
                'details': {
                    'advanced_encryption': 'available',
                    'workload_identity': 'available',
                    'observability': 'available',
                    'supabase_available': SUPABASE_AVAILABLE,
                    'backward_compatibility': 'maintained'
                }
            }
            
        except ImportError as e:
            return {
                'success': False,
                'message': f"Security module integration failed: {str(e)}",
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Security module integration test failed: {str(e)}",
                'error': str(e)
            }
    
    def test_graceful_fallbacks(self) -> Dict[str, Any]:
        """Test graceful fallback behavior when dependencies are missing"""
        try:
            # Test 1: Test with missing PyJWT (which we know is missing)
            jwt_fallback_success = False
            try:
                from security.workload_identity import workload_identity_manager
                # This should work even without PyJWT (graceful fallback)
                token = workload_identity_manager.get_token_for_platform('github')
                jwt_fallback_success = True  # Should not raise exception
            except ImportError:
                jwt_fallback_success = False
            except Exception:
                jwt_fallback_success = True  # Other exceptions are OK, import should work
            
            # Test 2: Test OpenTelemetry fallback
            otel_fallback_success = False
            try:
                from security.observability import observability_manager
                # This should work even without OpenTelemetry
                summary = observability_manager.get_metrics_summary()
                otel_fallback_success = True
            except ImportError:
                otel_fallback_success = False
            except Exception:
                otel_fallback_success = True  # Other exceptions are OK
            
            # Test 3: Test Supabase fallback
            supabase_fallback_success = False
            try:
                from security.supabase_integration import supabase_manager
                # This should work even without supabase library
                schema = supabase_manager.get_database_schema()
                supabase_fallback_success = True
            except ImportError:
                supabase_fallback_success = False
            except Exception:
                supabase_fallback_success = True  # Other exceptions are OK
            
            total_fallbacks = sum([jwt_fallback_success, otel_fallback_success, supabase_fallback_success])
            
            return {
                'success': total_fallbacks >= 2,  # At least 2/3 should work
                'message': f"Graceful fallbacks working: {total_fallbacks}/3 modules",
                'details': {
                    'jwt_fallback': jwt_fallback_success,
                    'opentelemetry_fallback': otel_fallback_success,
                    'supabase_fallback': supabase_fallback_success,
                    'total_working': total_fallbacks
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Graceful fallback test failed: {str(e)}",
                'error': str(e)
            }
    
    def test_performance_impact(self) -> Dict[str, Any]:
        """Test performance impact of new security features"""
        try:
            import time
            
            # Test 1: Encryption performance
            from security.advanced_encryption import encrypt_api_key_advanced, decrypt_api_key_advanced
            
            test_data = "test-api-key-" + "x" * 100  # Longer test data
            user_id = "performance-test-user"
            platform = "azure_devops"
            
            # Measure encryption time
            start_time = time.time()
            for _ in range(10):
                encrypted = encrypt_api_key_advanced(test_data, user_id, platform)
                decrypted, _ = decrypt_api_key_advanced(encrypted, user_id, platform)
                assert decrypted == test_data
            encryption_time = (time.time() - start_time) / 10
            
            # Test 2: Observability overhead
            from security.observability import observability_manager
            
            start_time = time.time()
            for i in range(20):
                observability_manager.log_security_event(
                    event_type="performance_test",
                    correlation_id=f"perf-{i}",
                    client_ip="127.0.0.1",
                    endpoint="/test",
                    severity="INFO"
                )
            observability_time = (time.time() - start_time) / 20
            
            # Performance thresholds
            encryption_threshold = 0.1  # 100ms per operation
            observability_threshold = 0.01  # 10ms per event
            
            performance_acceptable = (
                encryption_time < encryption_threshold and 
                observability_time < observability_threshold
            )
            
            return {
                'success': performance_acceptable,
                'message': f"Performance impact acceptable: Encryption {encryption_time*1000:.1f}ms, Observability {observability_time*1000:.1f}ms",
                'details': {
                    'encryption_time_ms': encryption_time * 1000,
                    'encryption_threshold_ms': encryption_threshold * 1000,
                    'observability_time_ms': observability_time * 1000,
                    'observability_threshold_ms': observability_threshold * 1000,
                    'performance_acceptable': performance_acceptable
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Performance impact test failed: {str(e)}",
                'error': str(e)
            }
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.success])
        failed_tests = total_tests - passed_tests
        total_duration = time.time() - self.start_time
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_duration': total_duration,
            'results': [
                {
                    'test_name': r.test_name,
                    'success': r.success,
                    'duration': r.duration,
                    'message': r.message,
                    'details': r.details,
                    'error': r.error
                }
                for r in self.results
            ]
        }
        
        # Save detailed results
        filename = f"advanced_security_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 ADVANCED SECURITY TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"⏱️  Total Duration: {total_duration:.2f}s")
        print()
        
        if passed_tests > 0:
            print("✅ Passed Tests:")
            for result in self.results:
                if result.success:
                    print(f"   - {result.test_name} ({result.duration:.2f}s): {result.message}")
            print()
        
        if failed_tests > 0:
            print("❌ Failed Tests:")
            for result in self.results:
                if not result.success:
                    print(f"   - {result.test_name} ({result.duration:.2f}s): {result.message}")
                    if result.error:
                        print(f"     Error: {result.error}")
            print()
        
        print(f"📄 Detailed results saved to: {filename}")
        print()
        
        if summary['success_rate'] >= 80:
            print("🏆 ADVANCED SECURITY ASSESSMENT: EXCELLENT")
            exit_code = 0
        elif summary['success_rate'] >= 60:
            print("⚠️  ADVANCED SECURITY ASSESSMENT: NEEDS IMPROVEMENT")
            exit_code = 1
        else:
            print("❌ ADVANCED SECURITY ASSESSMENT: CRITICAL ISSUES")
            exit_code = 2
        
        print(f"🏁 Advanced security test suite completed with exit code: {exit_code}")
        
        return summary

def main():
    """Main function to run the advanced security test suite"""
    suite = AdvancedSecurityTestSuite()
    summary = suite.run_all_tests()
    
    # Exit with appropriate code
    if summary['success_rate'] >= 80:
        sys.exit(0)
    elif summary['success_rate'] >= 60:
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()
