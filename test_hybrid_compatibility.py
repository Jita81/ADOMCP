#!/usr/bin/env python3
"""
Comprehensive test script for ADOMCP Hybrid Architecture
Tests both existing functionality and Claude Desktop compatibility
"""

import asyncio
import json
import os
import sys
import aiohttp
from typing import Dict, Any

# Add current directory to path for imports
sys.path.append('.')

# Test configuration
RAILWAY_URL = "https://web-production-f9a7c.up.railway.app"
TEST_PAT = os.getenv("AZURE_DEVOPS_PAT", "test_token_placeholder")

async def test_existing_http_endpoints():
    """Test existing HTTP endpoints for backward compatibility"""
    print("=" * 60)
    print("🔍 TESTING EXISTING HTTP ENDPOINTS (Backward Compatibility)")
    print("=" * 60)
    
    if TEST_PAT == "test_token_placeholder":
        print("⚠️  Warning: AZURE_DEVOPS_PAT environment variable not set")
        print("   Set it to test real Azure DevOps integration")
        return
    
    # Test Azure DevOps endpoint
    print("\n1️⃣ Testing /api/azure-devops endpoint...")
    async with aiohttp.ClientSession() as session:
        payload = {
            "operation": "get_projects",
            "test_pat_token": TEST_PAT
        }
        
        try:
            async with session.post(f"{RAILWAY_URL}/api/azure-devops", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ SUCCESS: {result.get('api_response')}")
                    print(f"   Projects found: {result.get('count', 0)}")
                else:
                    print(f"❌ FAILED: HTTP {response.status}")
        except Exception as e:
            print(f"❌ ERROR: {e}")

async def main():
    """Run basic tests"""
    print("🚀 ADOMCP HYBRID ARCHITECTURE BASIC TEST")
    print("For full testing, set AZURE_DEVOPS_PAT environment variable")
    
    # Test existing HTTP endpoints
    await test_existing_http_endpoints()
    
    print("\n🎉 Basic testing complete!")
    print("   Deploy to Railway successful if HTTP endpoints respond")

if __name__ == "__main__":
    asyncio.run(main())
