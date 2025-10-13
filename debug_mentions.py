#!/usr/bin/env python3
import sys
sys.path.append('src')
from twitter_factory import make_twitter_client

print('🔍 Testing mentions fetch...')
client = make_twitter_client()
mentions = client.get_mentions()
print(f'Found {len(mentions)} mentions')

for i, mention in enumerate(mentions[:3]):
    print(f'\nMention {i+1}:')
    print(f'  ID: {mention.get("id")}')
    print(f'  Text: {mention.get("text", "No text")}')
    print(f'  Author ID: {mention.get("author_id")}')
    if 'author' in mention:
        print(f'  Author: @{mention["author"]["username"]}')
    print(f'  Created: {mention.get("created_at")}')

