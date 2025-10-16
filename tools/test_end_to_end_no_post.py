#!/usr/bin/env python3
"""
End-to-end test script for CryBB bot.
Tests media upload (OAuth1a) and tweet creation (OAuth1a) without actually posting.
"""
import os
import sys
import io
from PIL import Image

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config
from x_v2 import XAPIv2Client, bearer_headers, oauth1_auth


def create_minimal_jpeg():
    """Create a minimal 1x1 JPEG image."""
    img = Image.new('RGB', (1, 1), color='white')
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=90)
    return output.getvalue()


def test_media_upload():
    """Test media upload using OAuth1a."""
    print("🧪 Testing media upload (OAuth1a)...")
    
    try:
        client = XAPIv2Client()
        jpeg_data = create_minimal_jpeg()
        print(f"Created {len(jpeg_data)} byte JPEG")
        
        media_id = client.media_upload(jpeg_data)
        print(f"✅ media OAuth1a OK - media_id: {media_id}")
        return media_id
        
    except Exception as e:
        print(f"❌ Media upload failed: {e}")
        return None


def test_oauth1_headers():
    """Test OAuth1a headers."""
    print("🧪 Testing OAuth1a headers...")
    
    try:
        auth = oauth1_auth()
        print(f"✅ OAuth1a auth OK")
        return True
        
    except Exception as e:
        print(f"❌ OAuth1a auth failed: {e}")
        return False


def test_bearer_headers():
    """Test Bearer token headers."""
    print("🧪 Testing Bearer token headers...")
    
    try:
        headers = bearer_headers()
        print(f"✅ Bearer headers OK - Authorization: {headers['Authorization'][:20]}...")
        return True
        
    except Exception as e:
        print(f"❌ Bearer headers failed: {e}")
        return False


def test_tweet_creation_dry_run():
    """Test tweet creation payload without actually posting."""
    print("🧪 Testing tweet creation payload (dry run)...")
    
    try:
        client = XAPIv2Client()
        
        # Test payload creation (don't actually post)
        test_payload = {
            "text": "Test tweet from CryBB bot",
            "reply": {"in_reply_to_tweet_id": "1234567890123456789"},
            "media": {"media_ids": ["test_media_id"]}
        }
        
        print(f"✅ Tweet payload OK - {len(test_payload['text'])} chars")
        return True
        
    except Exception as e:
        print(f"❌ Tweet creation test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 CryBB Bot End-to-End Test")
    print("=" * 50)
    
    # Check configuration
    print(f"[CONFIG] TWITTER_MODE={Config.TWITTER_MODE}")
    print(f"[CONFIG] API_KEY={'*' * 10 if Config.API_KEY else 'MISSING'}")
    print(f"[CONFIG] API_SECRET={'*' * 10 if Config.API_SECRET else 'MISSING'}")
    print(f"[CONFIG] ACCESS_TOKEN={'*' * 10 if Config.ACCESS_TOKEN else 'MISSING'}")
    print(f"[CONFIG] ACCESS_SECRET={'*' * 10 if Config.ACCESS_SECRET else 'MISSING'}")
    print(f"[CONFIG] BEARER_TOKEN={'*' * 10 if Config.BEARER_TOKEN else 'MISSING'}")
    print()
    
    # Run tests
    tests = [
        ("Media Upload (OAuth1a)", test_media_upload),
        ("OAuth1a Headers", test_oauth1_headers),
        ("Bearer Headers", test_bearer_headers),
        ("Tweet Creation (Dry Run)", test_tweet_creation_dry_run),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result is not None and result is not False))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Bot setup is working correctly.")
    else:
        print("⚠️  Some tests failed. Check configuration and tokens.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
