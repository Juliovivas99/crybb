#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from twitter_factory import make_twitter_client
from config import Config


def main() -> int:
    client = make_twitter_client()
    bot_id, bot_handle = client.get_bot_identity()
    tweets = client.get_user_tweets(bot_id, max_results=20)
    threshold = Config.RT_LIKE_THRESHOLD
    for t in tweets:
        likes = (t.get('public_metrics') or {}).get('like_count', 0)
        if likes >= threshold:
            print(f"Candidate tweet id={t.get('id')} likes={likes}")
            return 0
    print("No candidate found above threshold")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())


