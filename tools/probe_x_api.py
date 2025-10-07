#!/usr/bin/env python3
"""
Probe current X (Twitter) API capabilities using existing .env credentials.

Checks (prints PASS/FAIL):
  1) Auth: get_me (v2)
  2) Read mentions: recent mentions (v2)
  3) Lookup user: get_user(username=BOT_HANDLE) (v2)
  4) Download PFP: requests.get(profile_image_url)
  5) Media upload only: v1.1 media_upload from bytes (no tweet)

Exit codes:
  0  all required probes passed
  1  one or more probes failed
"""

import os
import sys
import time
import io
from typing import Optional, Tuple

import requests
import tweepy
from dotenv import load_dotenv


def load_env() -> Tuple[str, str, str, str, str, str]:
    """Load required environment variables from .env without enforcing repo Config validation."""
    load_dotenv()
    api_key = os.getenv("API_KEY", "")
    api_secret = os.getenv("API_SECRET", "")
    access_token = os.getenv("ACCESS_TOKEN", "")
    access_secret = os.getenv("ACCESS_SECRET", "")
    bearer_token = os.getenv("BEARER_TOKEN", "")
    bot_handle = os.getenv("BOT_HANDLE", "crybbmaker").lstrip("@")
    return api_key, api_secret, access_token, access_secret, bearer_token, bot_handle


def make_clients(api_key: str, api_secret: str, access_token: str, access_secret: str, bearer_token: str) -> Tuple[tweepy.API, tweepy.Client]:
    """Create Tweepy v1.1 and v2 clients."""
    v1_auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    v1_client = tweepy.API(v1_auth, wait_on_rate_limit=True)

    v2_client = tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
        wait_on_rate_limit=True,
    )
    return v1_client, v2_client


def with_retry(func, *, retries: int = 1, sleep_seconds: float = 3.0):
    """Run a callable with a single retry on TooManyRequests or transient errors."""
    try:
        return func()
    except tweepy.TooManyRequests as e:
        if retries > 0:
            time.sleep(sleep_seconds)
            return with_retry(func, retries=retries - 1, sleep_seconds=sleep_seconds)
        raise
    except requests.RequestException as e:
        if retries > 0:
            time.sleep(sleep_seconds)
            return with_retry(func, retries=retries - 1, sleep_seconds=sleep_seconds)
        raise


def probe_auth(v2_client: tweepy.Client) -> Tuple[bool, Optional[str], Optional[int]]:
    try:
        resp = with_retry(lambda: v2_client.get_me(user_fields=["username"]))
        if resp and resp.data:
            print(f"[PASS] AUTH get_me: @{resp.data.username} (id={resp.data.id})")
            return True, resp.data.username, resp.data.id
        print("[FAIL] AUTH get_me: empty response")
        return False, None, None
    except Exception as e:
        print(f"[FAIL] AUTH get_me: {e}")
        return False, None, None


def probe_read_mentions(v2_client: tweepy.Client, bot_handle: str, since_id: Optional[int] = None) -> bool:
    try:
        params = {
            "expansions": ["author_id", "in_reply_to_user_id"],
            "user_fields": ["username"],
            "tweet_fields": ["created_at", "author_id"],
            "max_results": 5,
        }
        if since_id:
            params["since_id"] = since_id
        resp = with_retry(lambda: v2_client.search_recent_tweets(query=f"@{bot_handle}", **params))
        count = len(resp.data) if resp and resp.data else 0
        print(f"[PASS] READ mentions: {count} found")
        return True
    except tweepy.Forbidden as e:
        print(f"[FAIL] READ mentions: 403 Forbidden - {e}")
        return False
    except Exception as e:
        print(f"[FAIL] READ mentions: {e}")
        return False


def probe_lookup_user(v2_client: tweepy.Client, bot_handle: str) -> Tuple[bool, Optional[str]]:
    try:
        user = with_retry(lambda: v2_client.get_user(username=bot_handle, user_fields=["profile_image_url"]))
        if user and user.data:
            pfp = user.data.profile_image_url
            print(f"[PASS] LOOKUP user @{bot_handle}: profile_image_url={'present' if pfp else 'missing'}")
            return True, pfp
        print(f"[FAIL] LOOKUP user @{bot_handle}: not found")
        return False, None
    except Exception as e:
        print(f"[FAIL] LOOKUP user @{bot_handle}: {e}")
        return False, None


def download_pfp(url: str) -> Tuple[bool, Optional[bytes]]:
    try:
        # Upgrade _normal to full-size if present
        if url and "_normal" in url:
            url = url.replace("_normal", "")
        resp = with_retry(lambda: requests.get(url, timeout=30))
        if resp.status_code == 200 and resp.content:
            print(f"[PASS] DOWNLOAD PFP: {len(resp.content)} bytes")
            return True, resp.content
        print(f"[FAIL] DOWNLOAD PFP: status={resp.status_code}")
        return False, None
    except Exception as e:
        print(f"[FAIL] DOWNLOAD PFP: {e}")
        return False, None


def probe_media_upload(v1_client: tweepy.API, image_bytes: bytes) -> bool:
    try:
        media = with_retry(lambda: v1_client.media_upload(filename="probe.jpg", file=io.BytesIO(image_bytes)))
        if getattr(media, "media_id", None):
            print(f"[PASS] MEDIA UPLOAD: media_id={media.media_id}")
            return True
        print("[FAIL] MEDIA UPLOAD: no media_id returned")
        return False
    except tweepy.Forbidden as e:
        print(f"[FAIL] MEDIA UPLOAD: 403 Forbidden - {e}")
        return False
    except Exception as e:
        print(f"[FAIL] MEDIA UPLOAD: {e}")
        return False


def main() -> int:
    api_key, api_secret, access_token, access_secret, bearer_token, bot_handle = load_env()

    v1_client, v2_client = make_clients(api_key, api_secret, access_token, access_secret, bearer_token)

    auth_ok, me_username, me_id = probe_auth(v2_client)

    # If auth fails, we cannot proceed
    read_ok = False
    lookup_ok = False
    download_ok = False
    upload_ok = False

    pfp_url = None
    image_bytes = None

    if auth_ok:
        read_ok = probe_read_mentions(v2_client, bot_handle)
        lookup_ok, pfp_url = probe_lookup_user(v2_client, bot_handle)

        # Fallback to authenticated user's PFP if bot_handle lookup missing
        if not pfp_url and me_id:
            try:
                me = with_retry(lambda: v2_client.get_user(id=me_id, user_fields=["profile_image_url"]))
                if me and me.data and me.data.profile_image_url:
                    pfp_url = me.data.profile_image_url
                    print("[INFO] Using authenticated user's profile_image_url as fallback")
            except Exception as e:
                print(f"[WARN] Fallback profile_image_url fetch failed: {e}")

        if pfp_url:
            download_ok, image_bytes = download_pfp(pfp_url)
        else:
            print("[FAIL] DOWNLOAD PFP: no profile_image_url available")

        if download_ok and image_bytes:
            upload_ok = probe_media_upload(v1_client, image_bytes)

    summary = f"AUTH:[{'ok' if auth_ok else 'fail'}] READ:[{'ok' if read_ok else 'fail'}] MEDIA_UPLOAD:[{'ok' if upload_ok else 'fail'}]"
    print("\n=== SUMMARY ===")
    print(summary)

    # Exit non-zero if any mandatory step fails
    if not (auth_ok and read_ok and upload_ok):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())



