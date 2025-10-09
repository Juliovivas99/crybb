#!/usr/bin/env python3
"""
Media upload smoke test using OAuth1a for v1.1 endpoint.
Tests the hybrid authentication approach: OAuth1a for media upload, OAuth2 for v2 endpoints.
"""
import os
import io
import requests
from requests_oauthlib import OAuth1
from dotenv import load_dotenv
from PIL import Image

# Load environment variables from .env file
load_dotenv()

def create_minimal_jpeg():
    """Create a minimal 1x1 JPEG image."""
    img = Image.new('RGB', (1, 1), color='white')
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=90)
    return output.getvalue()

def oauth1():
    """Create OAuth1 authentication object."""
    required = ["API_KEY", "API_SECRET", "ACCESS_TOKEN", "ACCESS_SECRET"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise SystemExit(f"Missing env vars for OAuth1: {', '.join(missing)}")
    return OAuth1(
        os.getenv("API_KEY"),
        os.getenv("API_SECRET"),
        os.getenv("ACCESS_TOKEN"),
        os.getenv("ACCESS_SECRET"),
    )

def main():
    """Test media upload with OAuth1a."""
    print("Testing media upload with OAuth1a...")
    
    # Create minimal JPEG
    jpeg_data = create_minimal_jpeg()
    print(f"Created {len(jpeg_data)} byte JPEG")
    
    url = "https://upload.twitter.com/1.1/media/upload.json"
    files = {"media": ("pixel.jpg", jpeg_data, "image/jpeg")}
    
    try:
        resp = requests.post(url, files=files, auth=oauth1(), timeout=30)
        print("status:", resp.status_code)
        print("body:", resp.text[:400])
        
        resp.raise_for_status()
        
        data = resp.json()
        mid = data.get("media_id_string")
        if not mid:
            raise SystemExit("No media_id_string in response")
        
        print("✅ media_id_string:", mid)
        print("✅ Media upload test passed!")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:400]}")
        raise SystemExit(1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
