#!/usr/bin/env python3
"""
Lightweight CLI tool to check CryBB bot queue state.
Shows since_id, processed tweet count, and estimated unprocessed mentions.
"""
import sys
import os
sys.path.append('src')

from storage import Storage
from twitter_factory import make_twitter_client
from config import Config

def main():
    """Check and display queue state."""
    print("🔍 CryBB Bot Queue State Check")
    print("=" * 40)
    
    try:
        # Initialize storage and client
        storage = Storage()
        client = make_twitter_client()
        
        # Get since_id
        since_id = storage.read_since_id()
        print(f"since_id = {since_id or 'None (no mentions processed yet)'}")
        
        # Get processed IDs count
        processed_ids = storage.read_processed_ids()
        processed_count = len(processed_ids)
        print(f"processed_ids = {processed_count}")
        
        # Estimate unprocessed mentions
        if since_id:
            try:
                # Get recent mentions to estimate queue size
                bot_id, _ = client.get_bot_identity()
                mentions = client.get_mentions(since_id)
                
                if isinstance(mentions, dict) and mentions.get("rate_limited"):
                    print("unprocessed_mentions = Rate limited (unable to check)")
                else:
                    unprocessed_count = len(mentions) if mentions else 0
                    print(f"unprocessed_mentions = {unprocessed_count}")
                    
                    # Show breakdown
                    if unprocessed_count > 0:
                        print(f"\n📊 Queue Breakdown:")
                        print(f"  • Total mentions since {since_id}: {unprocessed_count}")
                        print(f"  • Already processed: {processed_count}")
                        print(f"  • Pending processing: {unprocessed_count}")
            except Exception as e:
                print(f"unprocessed_mentions = Error checking: {e}")
        else:
            print("unprocessed_mentions = No since_id (first run)")
        
        # Show recent processed IDs (last 5)
        if processed_ids:
            recent_ids = sorted(processed_ids)[-5:]
            print(f"\n📝 Recent processed tweets (last 5):")
            for tweet_id in recent_ids:
                print(f"  • {tweet_id}")
        
        # Show configuration
        print(f"\n⚙️  Configuration:")
        print(f"  • Bot handle: @{Config.BOT_HANDLE}")
        print(f"  • Twitter mode: {Config.TWITTER_MODE}")
        print(f"  • Per-user limit: {Config.PER_USER_HOURLY_LIMIT}/hour")
        print(f"  • Whitelist: {', '.join(Config.WHITELIST_HANDLES)}")
        
    except Exception as e:
        print(f"❌ Error checking queue state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
