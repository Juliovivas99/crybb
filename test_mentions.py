#!/usr/bin/env python3
"""
Test script to check if mentions are being fetched
"""
import sys
sys.path.append('src')

from src.twitter_client_v2 import TwitterClientV2

def test_mentions():
    print("🔍 Testing mentions fetch...")
    
    client = TwitterClientV2()
    
    # Get mentions
    mentions = client.get_mentions()
    print(f"Found {len(mentions)} mentions")
    
    for i, mention in enumerate(mentions):
        print(f"\nMention {i+1}:")
        print(f"  ID: {mention.get('id')}")
        print(f"  Text: {mention.get('text')}")
        print(f"  Author ID: {mention.get('author_id')}")
        if 'author' in mention:
            print(f"  Author: @{mention['author']['username']}")
        print(f"  Created: {mention.get('created_at')}")

if __name__ == "__main__":
    test_mentions()

