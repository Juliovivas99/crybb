#!/usr/bin/env python3
"""
Authentication path verification for CryBB Maker Bot.
Reads use Bearer token; writes (media upload, tweet create) use OAuth 1.0a.
Does NOT post any tweets beyond auth checks.
"""
import os
import sys
import io
import base64
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
from config import Config
from x_v2 import XAPIv2Client, bearer_headers, oauth1_auth
import requests

def mask_token(token: str, show_chars: int = 4) -> str:
    """Mask a token showing only first and last few characters."""
    if not token or len(token) < show_chars * 2:
        return "***"
    return f"{token[:show_chars]}...{token[-show_chars:]}"

def create_tiny_png() -> bytes:
    """Create a tiny 1x1 PNG in memory."""
    # Minimal PNG data for a 1x1 transparent pixel
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return png_data

def test_bearer_token():
    """Test Bearer token authentication with v2 API."""
    print("🔐 Testing Bearer Token Authentication (v2 API)")
    print(f"   Bot Handle: @{Config.BOT_HANDLE}")
    print(f"   Bearer Token: {mask_token(Config.BEARER_TOKEN)}")
    
    try:
        url = f"https://api.twitter.com/2/users/by/username/{Config.BOT_HANDLE}"
        params = {
            'user.fields': 'id,username,name'
        }
        response = requests.get(url, headers=bearer_headers(), params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                user_data = data['data']
                print(f"✅ Bearer token working!")
                print(f"   User ID: {user_data['id']}")
                print(f"   Username: @{user_data['username']}")
                print(f"   Name: {user_data['name']}")
                
                # Print rate limit headers
                limit = response.headers.get('x-rate-limit-limit', 'N/A')
                remaining = response.headers.get('x-rate-limit-remaining', 'N/A')
                reset = response.headers.get('x-rate-limit-reset', 'N/A')
                print(f"   Rate Limit: {remaining}/{limit} remaining, resets at {reset}")
                
                return True, user_data['id']
            else:
                print(f"❌ No user data in response: {data}")
                return False, None
        else:
            print(f"❌ Bearer token failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Bearer token test failed: {e}")
        return False, None

def test_oauth1_verify_credentials():
    """Test OAuth 1.0a with verify_credentials."""
    print("\n🔑 Testing OAuth 1.0a verify_credentials")
    try:
        url = "https://api.twitter.com/1.1/account/verify_credentials.json"
        r = requests.get(url, auth=oauth1_auth(), timeout=30)
        print(f"   auth=OAuth1a GET {url} status={r.status_code}")
        r.raise_for_status()
        data = r.json()
        print(f"✅ OAuth1a verify_credentials OK: @{data['screen_name']} id={data['id_str']}")
        return True, data['id_str']
    except Exception as e:
        print(f"❌ OAuth1a verify_credentials failed: {e}")
        return False, None

def test_media_upload_v11():
    """Test v1.1 media upload with OAuth1a."""
    print("\n📷 Testing media upload v1.1 (OAuth1a)")
    
    try:
        client = XAPIv2Client()
        
        # Create tiny PNG
        png_data = create_tiny_png()
        print(f"   Created tiny PNG: {len(png_data)} bytes")
        
        media_id = client.media_upload(png_data)
        
        if media_id:
            print(f"✅ v1.1 media upload working!")
            print(f"   Media ID: {media_id}")
            return True, media_id
        else:
            print(f"❌ v2 media upload failed")
            return False, None
            
    except Exception as e:
        print(f"❌ v2 media upload test failed: {e}")
        return False, None

def test_tweet_creation_dry_run(media_id: str):
    """Build tweet payload as a dry run, confirm OAuth1a path."""
    print("\n🐦 Testing Tweet Creation (DRY RUN)")
    print("   Building tweet JSON, would use OAuth1a POST /2/tweets...")
    
    try:
        # Build tweet JSON payload
        tweet_data = {
            "text": "🧪 CryBB Maker Bot v2 authentication test - this tweet was NOT sent",
            "reply": {
                "in_reply_to_tweet_id": "1234567890123456789"  # Fake tweet ID
            },
            "media": {
                "media_ids": [media_id]
            }
        }
        
        print(f"✅ Tweet JSON payload built successfully:")
        print(f"   Text: {tweet_data['text']}")
        print(f"   Reply to: {tweet_data['reply']['in_reply_to_tweet_id']}")
        print(f"   Media IDs: {tweet_data['media']['media_ids']}")
        
        print(f"✅ tweet creation payload ready")
        print(f"   (Would be sent via POST /2/tweets with OAuth1a)")
        
        return True
        
    except Exception as e:
        print(f"❌ v2 tweet dry run failed: {e}")
        return False

def main():
    """Run all authentication path tests."""
    print("🚀 CryBB Maker Bot v2 Authentication Path Verification")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Bot Handle: @{Config.BOT_HANDLE}")
    print(f"Client ID: {mask_token(Config.CLIENT_ID)}")
    print(f"Bearer Token: {mask_token(Config.BEARER_TOKEN)}")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Validate configuration
    try:
        Config.validate()
        print("✅ Configuration validated successfully")
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return 1
    
    # Test Bearer token
    bearer_success, bot_id = test_bearer_token()
    if not bearer_success:
        print("\n❌ Bearer token test failed - stopping")
        return 1
    
    # Test OAuth 1.0a verify_credentials
    oauth1_success, user_id = test_oauth1_verify_credentials()
    if not oauth1_success:
        print("\n❌ OAuth1a verify_credentials failed - stopping")
        return 1
    
    # Test media upload v1.1
    media_success, media_id = test_media_upload_v11()
    if not media_success:
        print("\n❌ v2 media upload test failed - stopping")
        return 1
    
    # Test tweet creation (dry run)
    tweet_success = test_tweet_creation_dry_run(media_id)
    if not tweet_success:
        print("\n❌ v2 tweet dry run failed - stopping")
        return 1
    
    print("\n" + "=" * 60)
    print("🎉 ALL AUTHENTICATION TESTS PASSED!")
    print("✅ Bearer token (v2 API reads) - Working")
    print("✅ OAuth 1.0a (writes) - Working")
    print("✅ v1.1 media upload - Working")
    print("✅ v2 tweet creation (POST /2/tweets via OAuth1a) - Ready")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
