#!/usr/bin/env python3
"""
Quick test script for the fixed Twitter API v2 client authentication
"""
import os
import sys
sys.path.append('src')

# Import with absolute path
from src.twitter_client_v2 import TwitterClientV2

def test_authentication():
    print("🧪 Testing fixed Twitter API v2 authentication...")
    
    try:
        # Create client
        client = TwitterClientV2()
        print("✅ Client created successfully")
        
        # Test bot identity (this will test OAuth 2.0 Bearer Token)
        print("🔍 Testing bot identity with OAuth 2.0 Bearer Token...")
        bot_id, bot_handle = client.get_bot_identity()
        print(f"✅ Bot identity: @{bot_handle} (ID: {bot_id})")
        
        # Test mentions (this will test OAuth 2.0 Bearer Token)
        print("🔍 Testing mentions fetch with OAuth 2.0 Bearer Token...")
        mentions = client.get_mentions()
        print(f"✅ Mentions fetched: {len(mentions)} found")
        
        # Test rate limit status
        rate_status = client.get_rate_limit_status()
        print(f"✅ Rate limit status: {rate_status}")
        
        print("🎉 All authentication tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_authentication()
    sys.exit(0 if success else 1)
