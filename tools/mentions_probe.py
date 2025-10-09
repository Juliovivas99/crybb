#!/usr/bin/env python3
"""
Mentions probe script for CryBB Maker Bot v2.
Read-only probe to test mentions fetching and analyze target parsing.
"""
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
from config import Config
from auth_v2 import create_bearer_session, create_user_session
from x_v2 import XAPIv2Client
from utils import extract_target_after_bot

def probe_mentions():
    """Probe mentions using the new v2 client."""
    print("📨 CryBB Maker Bot v2 Mentions Probe")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Bot Handle: @{Config.BOT_HANDLE}")
    print("=" * 50)
    
    try:
        # Initialize v2 client
        bearer_session = create_bearer_session()
        user_session = create_user_session()
        client = XAPIv2Client(bearer_session, user_session)
        
        # Get bot identity first
        print("\n🤖 Getting bot identity...")
        bot_id, bot_username = client.get_me()
        print(f"✅ Bot Identity: @{bot_username} (ID: {bot_id})")
        
        # Get mentions
        print("\n📨 Fetching mentions...")
        mentions = client.get_mentions(bot_id)
        
        print(f"✅ Retrieved {len(mentions)} mentions")
        
        if mentions:
            # Analyze each mention
            for i, mention in enumerate(mentions[:3]):  # Analyze first 3 mentions
                print(f"\n🔍 Analyzing mention {i+1}:")
                print(f"   Tweet ID: {mention['id']}")
                print(f"   Created: {mention.get('created_at', 'N/A')}")
                print(f"   Text: {mention.get('text', 'N/A')[:100]}...")
                
                # Check author info
                if 'author' in mention:
                    author = mention['author']
                    print(f"   Author: @{author['username']} ({author['name']})")
                    author_username = author['username']
                else:
                    author_username = "unknown"
                
                # Test target extraction
                print(f"\n🎯 Testing target extraction:")
                target_username = extract_target_after_bot(mention, Config.BOT_HANDLE, author_username)
                print(f"   Extracted target: @{target_username}")
                
                # Analyze mentions in the text
                if 'entities' in mention and 'mentions' in mention['entities']:
                    mentions_entities = mention['entities']['mentions']
                    print(f"\n📋 Mentions in tweet ({len(mentions_entities)} found):")
                    
                    for j, mention_entity in enumerate(mentions_entities):
                        print(f"   {j+1}. @{mention_entity.get('username', 'unknown')} (start: {mention_entity.get('start', 'N/A')}, end: {mention_entity.get('end', 'N/A')})")
                    
                    # Check for "first username after the bot" rule
                    if len(mentions_entities) > 1:
                        # Find bot mention position
                        bot_mention_pos = None
                        for mention_entity in mentions_entities:
                            if mention_entity.get('username', '').lower() == Config.BOT_HANDLE.lower():
                                bot_mention_pos = mention_entity.get('start', 0)
                                break
                        
                        if bot_mention_pos is not None:
                            # Find first mention after bot
                            after_bot_mentions = [m for m in mentions_entities if m.get('start', 0) > bot_mention_pos]
                            if after_bot_mentions:
                                first_after_bot = min(after_bot_mentions, key=lambda x: x.get('start', 0))
                                print(f"\n🎯 First username after bot: @{first_after_bot.get('username', 'unknown')}")
                                print(f"   Position: {first_after_bot.get('start', 'N/A')}-{first_after_bot.get('end', 'N/A')}")
                            else:
                                print(f"\n⚠️  No mentions found after bot mention")
                        else:
                            print(f"\n⚠️  Bot mention not found in entities")
                    else:
                        print(f"\n⚠️  Only {len(mentions_entities)} mention(s) found - need at least 2 for analysis")
                else:
                    print(f"\n⚠️  No mention entities found in tweet")
                
                # Show mentioned users data
                if 'mentioned_users' in mention:
                    print(f"\n👥 Mentioned users data:")
                    for username, user_data in mention['mentioned_users'].items():
                        print(f"   @{username}: {user_data.get('name', 'N/A')} (ID: {user_data.get('id', 'N/A')})")
                
                print("-" * 50)
        
        else:
            print("\n⚠️  No mentions found")
        
        # Show rate limit status
        print(f"\n📊 Rate limit status:")
        rate_status = client.get_rate_limit_status()
        for endpoint, info in rate_status.items():
            print(f"   {endpoint}: {info['remaining']}/{info['limit']} remaining, resets at {info['reset_time']}")
        
        print(f"\n✅ Mentions probe completed successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Mentions probe failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the mentions probe."""
    # Load environment variables
    load_dotenv()
    
    # Validate configuration
    try:
        Config.validate()
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return 1
    
    success = probe_mentions()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

