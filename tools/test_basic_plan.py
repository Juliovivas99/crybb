#!/usr/bin/env python3
"""
Verify Basic plan credentials and OAuth 2.0 flows for the CryBB bot.

Steps:
 1) OAuth 2.0 auth (using bearer token provided; Client Credentials token endpoint is not public for X API)
 2) /2/users/me
 3) /2/users/:id/mentions (limit 5)
 4) Resolve a mention's target username → user id
 5) Download target's profile image
 6) Media upload (v1.1) using a local test image
 7) Build (but do not send) a reply payload

Usage:
  python3 tools/test_basic_plan.py
"""
import io
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv


# Ensure repo root on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def print_line(tag: str, ok: bool, msg: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{tag}] {status}{' - ' + msg if msg else ''}")


def load_clients():
    import tweepy
    api_key = os.getenv("API_KEY", "")
    api_secret = os.getenv("API_SECRET", "")
    access_token = os.getenv("ACCESS_TOKEN", "")
    access_secret = os.getenv("ACCESS_SECRET", "")
    bearer_token = os.getenv("BEARER_TOKEN", "")

    v1_auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    v1 = tweepy.API(v1_auth, wait_on_rate_limit=True)

    v2 = tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
        wait_on_rate_limit=True,
    )
    return v1, v2


def get_me(v2) -> Tuple[bool, Optional[int], Optional[str], str]:
    try:
        me = v2.get_me(user_fields=["username"])  # type: ignore[attr-defined]
        if me and getattr(me, "data", None):
            return True, me.data.id, me.data.username, f"@{me.data.username} id={me.data.id}"
        return False, None, None, "Empty response"
    except Exception as e:
        return False, None, None, str(e)


def get_mentions(v2, uid: int) -> Tuple[bool, List[Any], str]:
    try:
        resp = v2.get_users_mentions(id=uid, max_results=5, tweet_fields=["author_id", "created_at"], expansions=["author_id"])  # type: ignore[attr-defined]
        tweets = resp.data or []
        return True, tweets, f"mentions returned: {len(tweets)}"
    except Exception as e:
        return False, [], str(e)


def resolve_target(v2, tweet) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    try:
        text = getattr(tweet, "text", "") or ""
        # Find the first @mention other than the bot; simple heuristic
        import re
        at = re.findall(r"@(\w+)", text)
        if not at:
            return False, None, "No @mention found in tweet text"
        target = at[0]
        me = v2.get_me(user_fields=["username"])  # type: ignore[attr-defined]
        if me and me.data and me.data.username and target.lower() == me.data.username.lower():
            if len(at) > 1:
                target = at[1]
            else:
                return False, None, "Only the bot was mentioned"
        u = v2.get_user(username=target, user_fields=["profile_image_url", "name", "username"])  # type: ignore[attr-defined]
        if u and getattr(u, "data", None):
            data = {"id": u.data.id, "username": u.data.username, "name": u.data.name, "profile_image_url": getattr(u.data, "profile_image_url", None)}
            return True, data, f"target id: {data['id']}"
        return False, None, "Target user lookup failed"
    except Exception as e:
        return False, None, str(e)


def download_image(url: Optional[str]) -> Tuple[bool, Optional[bytes], str]:
    try:
        if not url:
            return False, None, "No profile_image_url"
        if "_normal" in url:
            url = url.replace("_normal", "")
        import requests
        r = requests.get(url, timeout=30)
        size = len(r.content) if r.content else 0
        if r.status_code == 200 and size > 0:
            return True, r.content, f"{size // 1024} KB"
        return False, None, f"status={r.status_code} bytes={size}"
    except Exception as e:
        return False, None, str(e)


def media_upload(v1, image_bytes: Optional[bytes]) -> Tuple[bool, Optional[int], str]:
    try:
        if not image_bytes:
            # fallback to local test image
            local = os.path.join(ROOT_DIR, "fixtures", "images", "test_face.jpg")
            if not os.path.exists(local):
                return False, None, "fixtures/images/test_face.jpg missing"
            with open(local, "rb") as f:
                image_bytes = f.read()
        media = v1.media_upload(filename="probe.jpg", file=io.BytesIO(image_bytes))  # type: ignore[attr-defined]
        mid = getattr(media, "media_id", None)
        if mid:
            return True, int(mid), f"media_id: {mid}"
        return False, None, "No media_id returned"
    except Exception as e:
        return False, None, str(e)


def build_tweet_payload(in_reply_to_tweet_id: int, text: str, media_id: Optional[int]) -> Tuple[bool, Dict[str, Any], str]:
    try:
        payload: Dict[str, Any] = {"text": text}
        if media_id:
            payload["media"] = {"media_ids": [media_id]}
        payload["reply"] = {"in_reply_to_tweet_id": in_reply_to_tweet_id}
        return True, payload, json.dumps(payload)
    except Exception as e:
        return False, {}, str(e)


def main() -> int:
    load_dotenv()

    try:
        import tweepy  # noqa: F401
        import requests  # noqa: F401
    except Exception as e:
        print_line("INIT", False, f"Dependency error: {e}")
        return 1

    v1, v2 = load_clients()

    # 1) AUTH
    ok, me_id, me_username, msg = get_me(v2)
    print_line("AUTH", ok, msg)
    if not ok or not me_id:
        return 1

    # 2) READ mentions
    ok, tweets, msg = get_mentions(v2, me_id)
    print_line("READ", ok, msg)
    if not tweets:
        # Continue, but some later steps may be skipped
        tweets = []

    # 3) USER LOOKUP (from first mention if available)
    target_info: Optional[Dict[str, Any]] = None
    if tweets:
        ok, target_info, msg = resolve_target(v2, tweets[0])
        print_line("USER LOOKUP", ok, msg)
    else:
        # Fallback to a known user
        try:
            resp = v2.get_user(username="twitterdev", user_fields=["profile_image_url", "name", "username"])  # type: ignore[attr-defined]
            if resp and getattr(resp, "data", None):
                target_info = {"id": resp.data.id, "username": resp.data.username, "name": resp.data.name, "profile_image_url": getattr(resp.data, "profile_image_url", None)}
                print_line("USER LOOKUP", True, f"target id: {target_info['id']}")
            else:
                print_line("USER LOOKUP", False, "Could not lookup twitterdev")
        except Exception as e:
            print_line("USER LOOKUP", False, str(e))

    # 4) IMAGE DOWNLOAD
    img_bytes: Optional[bytes] = None
    ok, img_bytes, msg = download_image(target_info.get("profile_image_url") if target_info else None)
    print_line("IMAGE DOWNLOAD", ok, msg)

    # 5) MEDIA UPLOAD
    ok, media_id, msg = media_upload(v1, img_bytes)
    print_line("MEDIA UPLOAD", ok, msg)

    # 6) TWEET BUILD (dry-run)
    in_reply_to = tweets[0].id if tweets else 1234567890
    text = f"Here's your CryBB PFP @{target_info['username']} 🔥" if target_info else "Here's your CryBB PFP 🔥"
    ok, payload, msg = build_tweet_payload(in_reply_to, text, media_id if ok else None)
    print_line("TWEET BUILD", ok, "payload built" if ok else msg)

    return 0


if __name__ == "__main__":
    sys.exit(main())






