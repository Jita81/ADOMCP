#!/usr/bin/env python3
"""
Test Runner for ADOMCP
Runs regression tests and/or performance tests with options.
"""

import sys
import subprocess
import argparse
from datetime import datetime

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(command)}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    try:
        result = subprocess.run(command, check=False)
        success = result.returncode == 0
        
        print("-" * 60)
        print(f"{'✅ SUCCESS' if success else '❌ FAILED'} - Exit code: {result.returncode}")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='ADOMCP Test Runner')
    parser.add_argument('--regression', '-r', action='store_true', 
                       help='Run regression tests')
    parser.add_argument('--performance', '-p', action='store_true', 
                       help='Run performance tests')
    parser.add_argument('--all', '-a', action='store_true', 
                       help='Run all tests (regression + performance)')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='Run quick smoke test (basic endpoints only)')
    
    args = parser.parse_args()
    
    if not any([args.regression, args.performance, args.all, args.quick]):
        print("❌ No test type specified. Use --help for options.")
        sys.exit(1)
    
    print("🧪 ADOMCP Test Runner")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    if args.quick:
        # Quick smoke test - just check if server is up and endpoints work
        print("\n🔥 Running Quick Smoke Test...")
        quick_commands = [
            (["curl", "-s", "https://adomcp.vercel.app/"], "Server Health Check"),
            (["curl", "-s", "https://adomcp.vercel.app/health"], "Health Endpoint"),
            (["curl", "-s", "https://adomcp.vercel.app/api/test"], "API Test Endpoint"),
            (["curl", "-s", "https://adomcp.vercel.app/api/capabilities"], "Capabilities Endpoint")
        ]
        
        for command, description in quick_commands:
            success = run_command(command, description)
            results.append((description, success))
    
    if args.regression or args.all:
        success = run_command([sys.executable, "regression_tests.py"], "Regression Test Suite")
        results.append(("Regression Tests", success))
    
    if args.performance or args.all:
        success = run_command([sys.executable, "performance_tests.py"], "Performance Test Suite")
        results.append(("Performance Tests", success))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST RUNNER SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    print(f"Success rate: {(passed/total*100):.1f}%")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit with appropriate code
    exit_code = 0 if passed == total else 1
    print(f"\n🏁 Test runner completed with exit code: {exit_code}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
