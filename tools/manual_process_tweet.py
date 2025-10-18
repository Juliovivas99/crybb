#!/usr/bin/env python3
"""
Manual tweet processing script for debugging and recovery.
Usage: python tools/manual_process_tweet.py <tweet_id>
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set environment variables before importing modules
os.environ.setdefault('SKIP_CONFIG_VALIDATION', '1')

from src.main import CryBBBot
from src.batch_context import ProcessingContext
from src.config import Config
import requests

def manual_process_tweet(tweet_id: str):
    """Manually process a specific tweet."""
    bot = CryBBBot()
    ctx = ProcessingContext()
    
    # Fetch tweet data
    url = f'https://api.twitter.com/2/tweets/{tweet_id}'
    params = {
        'expansions': 'author_id,entities.mentions.username',
        'user.fields': 'id,username,name,profile_image_url',
        'tweet.fields': 'created_at,entities,author_id,in_reply_to_user_id'
    }
    headers = {'Authorization': f'Bearer {Config.BEARER_TOKEN}'}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"❌ Error fetching tweet {tweet_id}: {response.status_code}")
        return
    
    tweet_data = response.json()['data']
    includes = response.json().get('includes', {})
    
    # Add includes to tweet_data for processing
    tweet_data['includes'] = includes
    
    print(f"🚀 Manually processing tweet {tweet_id}")
    print(f"Text: {tweet_data['text']}")
    
    try:
        bot.process_mention(tweet_data, ctx)
        print("✅ Manual processing completed!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tools/manual_process_tweet.py <tweet_id>")
        sys.exit(1)
    
    tweet_id = sys.argv[1]
    manual_process_tweet(tweet_id)
