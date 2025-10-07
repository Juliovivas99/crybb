#!/usr/bin/env python3
"""
Run a single poll-and-process cycle honoring TWITTER_MODE (live/dryrun/mock).
Writes replies to outbox/ in dryrun/mock; live will actually post.
"""
import os
import sys
import time
from dotenv import load_dotenv

# Ensure package imports work when run directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import Config
from src.twitter_factory import make_twitter_client
from src.image_processor import ImageProcessor
from src.utils import extract_target_username, format_friendly_message


def main() -> int:
    load_dotenv()
    client = make_twitter_client()
    processor = ImageProcessor()

    bot_id, bot_handle = client.get_bot_identity()
    print(f"Mode={Config.TWITTER_MODE} Bot=@{bot_handle} ({bot_id})")

    mentions = client.get_mentions(None)
    if not mentions:
        print("No mentions found.")
        return 0

    # Process first mention only
    tweet = mentions[0]
    tweet_id = getattr(tweet, "id", int(time.time()))
    text = getattr(tweet, "text", "")
    author_id = getattr(tweet, "author_id", 0)
    print(f"Processing tweet {tweet_id} from {author_id}: {text}")

    # Determine target
    target = extract_target_username(text or "", bot_handle)
    if not target:
        user = client.get_user_by_id(int(author_id)) if author_id else None
        if user and user.get("username"):
            target = user["username"]

    # Get profile image url
    profile_url = None
    if target:
        u = client.get_user_by_username(target)
        profile_url = u.get("profile_image_url") if u else None
    if not profile_url and author_id:
        u = client.get_user_by_id(int(author_id))
        profile_url = u.get("profile_image_url") if u else None

    if not profile_url:
        print("No profile_image_url available; aborting.")
        return 1

    img_bytes = client.download_bytes(profile_url)
    if not img_bytes:
        print("Failed to download image bytes; aborting.")
        return 1

    out_bytes = processor.render(img_bytes, watermark=Config.WATERMARK_TEXT)
    reply_text = format_friendly_message(target)
    client.reply_with_image(tweet_id, reply_text, out_bytes)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


