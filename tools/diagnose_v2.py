#!/usr/bin/env python3
"""
Diagnostic script for CryBB Maker Bot full flow testing.
Simulates the complete mention-to-reply flow without actual posting.
"""

import sys
import os
import argparse
import json
import tempfile
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config
from utils import extract_target_after_bot, normalize_pfp_url, format_friendly_message
from pipeline.orchestrator import Orchestrator
from twitter_factory import make_twitter_client

def create_synthetic_mention(tweet_text: str) -> Dict[str, Any]:
    """Create synthetic mention data from tweet text."""
    
    # Parse mentions from text
    import re
    mentions = re.findall(r'@(\w+)', tweet_text)
    
    # Create entities structure
    entities_mentions = []
    current_pos = 0
    
    for mention in mentions:
        start = tweet_text.find(f"@{mention}", current_pos)
        end = start + len(f"@{mention}")
        entities_mentions.append({
            "start": start,
            "end": end,
            "username": mention
        })
        current_pos = end
    
    # Create synthetic mention data
    synthetic_data = {
        "data": {
            "id": "123456789",
            "text": tweet_text,
            "entities": {
                "mentions": entities_mentions
            },
            "author_id": "111111111",
            "created_at": "2024-01-01T00:00:00.000Z"
        },
        "includes": {
            "users": [
                {
                    "id": "111111111",
                    "username": "authoruser",
                    "name": "Author User",
                    "profile_image_url": "https://pbs.twimg.com/profile_images/123456789/author_normal.jpg"
                }
            ]
        }
    }
    
    # Add mentioned users to includes
    mentioned_users = {}
    for mention in mentions:
        if mention.lower() != "crybbmaker":
            user_id = f"222222222{len(mentioned_users)}"
            mentioned_users[mention] = {
                "id": user_id,
                "username": mention,
                "name": f"{mention.title()} User",
                "profile_image_url": f"https://pbs.twimg.com/profile_images/123456789/{mention}_normal.jpg"
            }
            synthetic_data["includes"]["users"].append(mentioned_users[mention])
    
    return synthetic_data

def simulate_mention_processing(tweet_text: str) -> Dict[str, Any]:
    """Simulate the complete mention processing flow."""
    
    print(f"🔍 Simulating mention processing for: {tweet_text}")
    print("=" * 60)
    
    # Create synthetic mention data
    mention_data = create_synthetic_mention(tweet_text)
    tweet_data = mention_data["data"]
    
    print("📝 Synthetic mention data:")
    print(json.dumps(mention_data, indent=2))
    print()
    
    # Step 1: Extract target
    print("🎯 Step 1: Extracting target...")
    author_username = "authoruser"  # From synthetic data
    target_username = extract_target_after_bot(tweet_data, Config.BOT_HANDLE, author_username)
    print(f"Target selected: {target_username}")
    
    # Step 2: Find target user data
    print("\n👤 Step 2: Finding target user data...")
    target_user_data = None
    
    # Look in mentioned_users (simulating expanded data)
    if 'mentioned_users' in tweet_data:
        target_user_data = tweet_data['mentioned_users'].get(target_username)
        print(f"Found target in mentioned_users: {target_user_data is not None}")
    
    # Fallback to includes
    if not target_user_data:
        for user in mention_data["includes"]["users"]:
            if user["username"] == target_username:
                target_user_data = user
                break
        print(f"Found target in includes: {target_user_data is not None}")
    
    if not target_user_data:
        print(f"❌ Could not find user data for @{target_username}")
        return {"error": "Target user not found"}
    
    print(f"Target user data: {target_user_data}")
    
    # Step 3: Normalize PFP URL
    print("\n🖼️  Step 3: Normalizing PFP URL...")
    original_pfp = target_user_data.get('profile_image_url', '')
    normalized_pfp = normalize_pfp_url(original_pfp)
    print(f"Original PFP: {original_pfp}")
    print(f"Normalized PFP: {normalized_pfp}")
    
    # Step 4: Check orchestrator configuration
    print("\n🎨 Step 4: Checking orchestrator configuration...")
    try:
        orchestrator = Orchestrator(Config)
        print(f"Image pipeline mode: {Config.IMAGE_PIPELINE}")
        print(f"CRYBB_STYLE_URL: {Config.CRYBB_STYLE_URL}")
        
        if Config.CRYBB_STYLE_URL:
            image_urls = [Config.CRYBB_STYLE_URL, normalized_pfp]
            print(f"Image URLs for nano-banana: {image_urls}")
        else:
            print("⚠️  CRYBB_STYLE_URL not configured")
            
    except Exception as e:
        print(f"❌ Orchestrator configuration error: {e}")
        return {"error": f"Orchestrator error: {e}"}
    
    # Step 5: Simulate image generation (without actual AI call)
    print("\n🤖 Step 5: Simulating image generation...")
    try:
        if Config.IMAGE_PIPELINE == "placeholder":
            print("Using placeholder mode - no AI generation")
            generated_image_path = "simulated_placeholder_image.jpg"
        else:
            print("Would call nano-banana AI with:")
            print(f"  - Style image: {Config.CRYBB_STYLE_URL}")
            print(f"  - Target PFP: {normalized_pfp}")
            generated_image_path = "simulated_ai_generated_image.jpg"
        
        print(f"Generated image path: {generated_image_path}")
        
    except Exception as e:
        print(f"❌ Image generation simulation error: {e}")
        return {"error": f"Image generation error: {e}"}
    
    # Step 6: Simulate reply creation
    print("\n💬 Step 6: Simulating reply creation...")
    reply_text = format_friendly_message(target_username)
    print(f"Reply text: {reply_text}")
    
    # Simulate reply payload
    reply_payload = {
        "text": reply_text,
        "reply": {
            "in_reply_to_tweet_id": tweet_data["id"]
        },
        "media": {
            "media_ids": ["simulated_media_id_12345"]
        }
    }
    
    print("Reply payload:")
    print(json.dumps(reply_payload, indent=2))
    
    # Summary
    print("\n📊 Summary:")
    print("=" * 60)
    print(f"✅ Target extraction: {target_username}")
    print(f"✅ PFP normalization: {normalized_pfp}")
    print(f"✅ Image generation: {generated_image_path}")
    print(f"✅ Reply text: {reply_text}")
    print(f"✅ Reply payload: Ready for Twitter API v2")
    
    return {
        "success": True,
        "target_username": target_username,
        "normalized_pfp": normalized_pfp,
        "generated_image_path": generated_image_path,
        "reply_text": reply_text,
        "reply_payload": reply_payload
    }

def test_twitter_client():
    """Test Twitter client functionality."""
    print("\n🐦 Testing Twitter client...")
    print("=" * 60)
    
    try:
        client = make_twitter_client()
        print(f"✅ Twitter client created: {type(client).__name__}")
        
        # Test bot identity
        bot_id, bot_handle = client.get_bot_identity()
        print(f"✅ Bot identity: @{bot_handle} (ID: {bot_id})")
        
        # Test rate limit status
        rate_status = client.get_rate_limit_status()
        print(f"✅ Rate limit status: {len(rate_status)} endpoints tracked")
        
        return True
        
    except Exception as e:
        print(f"❌ Twitter client test failed: {e}")
        return False

def main():
    """Main diagnostic function."""
    parser = argparse.ArgumentParser(description="Diagnose CryBB Maker Bot mention processing")
    parser.add_argument("--simulate-mention", type=str, 
                       help="Simulate processing for a specific mention text")
    parser.add_argument("--test-client", action="store_true",
                       help="Test Twitter client functionality")
    parser.add_argument("--all", action="store_true",
                       help="Run all tests")
    
    args = parser.parse_args()
    
    print("🔧 CryBB Maker Bot Diagnostic Tool")
    print("=" * 60)
    
    success = True
    
    if args.simulate_mention or args.all:
        result = simulate_mention_processing(args.simulate_mention or "@crybbmaker @targetuser make me #crybb")
        if "error" in result:
            success = False
    
    if args.test_client or args.all:
        if not test_twitter_client():
            success = False
    
    if not any([args.simulate_mention, args.test_client, args.all]):
        # Default: run simulation with example
        result = simulate_mention_processing("@crybbmaker @targetuser make me #crybb")
        if "error" in result:
            success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All diagnostics passed!")
        sys.exit(0)
    else:
        print("❌ Some diagnostics failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
