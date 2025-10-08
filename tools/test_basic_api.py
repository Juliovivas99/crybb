#!/usr/bin/env python3
"""
End-to-end Basic plan verification against X (Twitter) API using .env credentials.

Checks:
 1) Auth (v2 get_me)
 2) Mentions read (v2 users/:id/mentions, limit 5)
 3) User lookup (v2 by username e.g. twitterdev)
 4) Profile image download via requests
 5) Media upload only (v1.1 media_upload from bytes) — no tweet
 6) Dry-run simulation (run tools/simulate_once.py with TWITTER_MODE=dryrun)

Usage:
  python3 tools/test_basic_api.py
"""
import io
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv


# Ensure repo root in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def make_clients() -> Tuple["tweepy.API", "tweepy.Client"]:  # type: ignore[name-defined]
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


def result(name: str, passed: bool, details: str = "", evidence: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "details": details, "evidence": evidence or {}}


def print_table(results: List[Dict[str, Any]]) -> None:
    name_w = max(5, max(len(r["name"]) for r in results))
    print(f"{'CHECK'.ljust(name_w)}  STATUS  DETAILS")
    for r in results:
        n = r["name"].ljust(name_w)
        s = r["status"].ljust(6)
        d = (r.get("details") or "").replace("\n", " ")
        print(f"{n}  {s}  {d}")


def auth_check(v2) -> Dict[str, Any]:
    name = "Auth"
    try:
        me = v2.get_me(user_fields=["username"])  # type: ignore[attr-defined]
        if me and getattr(me, "data", None):
            username = me.data.username
            uid = me.data.id
            return result(name, True, f"@{username} (id={uid})")
        return result(name, False, "Empty response from get_me")
    except Exception as e:
        return result(name, False, f"{e}")


def mentions_check(v2, me_id: Optional[int]) -> Dict[str, Any]:
    name = "Mentions Read"
    try:
        if not me_id:
            # Fetch id if not provided
            me = v2.get_me()
            me_id = me.data.id if me and me.data else None
        if not me_id:
            return result(name, False, "Could not resolve me.id for mentions")
        params = {
            "expansions": ["author_id"],
            "tweet_fields": ["created_at", "author_id"],
            "max_results": 5,
        }
        resp = v2.get_users_mentions(id=me_id, **params)
        count = len(resp.data) if resp and getattr(resp, "data", None) else 0
        return result(name, True, f"{count} mentions")
    except Exception as e:
        return result(name, False, f"{e}")


def lookup_check(v2, username: str = "twitterdev") -> Tuple[Dict[str, Any], Optional[str]]:
    name = "User Lookup"
    try:
        resp = v2.get_user(username=username, user_fields=["profile_image_url", "name", "username"])  # type: ignore[attr-defined]
        if resp and getattr(resp, "data", None):
            data = resp.data
            details = f"@{data.username} id={data.id} name={data.name}"
            return result(name, True, details), getattr(data, "profile_image_url", None)
        return result(name, False, f"User not found: {username}"), None
    except Exception as e:
        return result(name, False, f"{e}"), None


def download_pfp_check(url: Optional[str]) -> Dict[str, Any]:
    name = "PFP Download"
    try:
        if not url:
            return result(name, False, "No profile_image_url available")
        if "_normal" in url:
            url = url.replace("_normal", "")
        import requests

        r = requests.get(url, timeout=30)
        size = len(r.content) if r.content else 0
        if r.status_code == 200 and size > 0:
            return result(name, True, f"status=200 bytes={size}")
        return result(name, False, f"status={r.status_code} bytes={size}")
    except Exception as e:
        return result(name, False, f"{e}")


def media_upload_check(v1) -> Dict[str, Any]:
    name = "Media Upload"
    try:
        # Generate a tiny JPEG in memory
        try:
            from PIL import Image
        except Exception as e:
            return result(name, False, f"Pillow not installed: {e}")
        img = Image.new("RGB", (64, 64), color=(200, 50, 50))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        buf.seek(0)

        media = v1.media_upload(filename="probe.jpg", file=buf)  # type: ignore[attr-defined]
        media_id = getattr(media, "media_id", None)
        if media_id:
            return result(name, True, f"media_id={media_id}")
        return result(name, False, "No media_id returned")
    except Exception as e:
        return result(name, False, f"{e}")


def dryrun_simulation_check() -> Dict[str, Any]:
    name = "Dry-Run Simulation"
    try:
        import subprocess
        env = os.environ.copy()
        env["TWITTER_MODE"] = "dryrun"
        env.setdefault("SKIP_CONFIG_VALIDATION", "1")
        p = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "tools", "simulate_once.py")], cwd=ROOT_DIR, env=env, capture_output=True, text=True)
        if p.returncode != 0:
            return result(name, False, f"simulate_once exit={p.returncode}: {p.stderr.strip()}")
        outbox_dir = os.path.join(ROOT_DIR, "outbox")
        if not os.path.isdir(outbox_dir):
            return result(name, False, "outbox/ not created")
        entries = sorted([d for d in os.listdir(outbox_dir) if os.path.isdir(os.path.join(outbox_dir, d))], reverse=True)
        if not entries:
            return result(name, False, "No outbox entries found")
        newest = os.path.join(outbox_dir, entries[0])
        files = os.listdir(newest)
        return result(name, True, f"outbox={os.path.basename(newest)} files={files}")
    except Exception as e:
        return result(name, False, f"{e}")


def main() -> int:
    load_dotenv()

    try:
        import tweepy  # noqa: F401
        import requests  # noqa: F401
    except Exception as e:
        print(f"Dependency error: {e}")
        return 1

    v1, v2 = make_clients()

    results: List[Dict[str, Any]] = []

    # 1) Auth
    r_auth = auth_check(v2)
    results.append(r_auth)
    me_id: Optional[int] = None
    if r_auth["status"] == "PASS":
        try:
            me = v2.get_me()
            me_id = me.data.id if me and me.data else None
        except Exception:
            me_id = None

    # 2) Mentions
    results.append(mentions_check(v2, me_id))

    # 3) Lookup twitterdev
    r_lookup, pfp_url = lookup_check(v2, "twitterdev")
    results.append(r_lookup)

    # 4) Download profile image
    results.append(download_pfp_check(pfp_url))

    # 5) Media upload (no tweet)
    results.append(media_upload_check(v1))

    # 6) Dry-run simulation
    results.append(dryrun_simulation_check())

    # Print summary table
    print()
    print_table(results)

    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    print()
    print(f"✅ Basic Plan API test complete: {passed}/{total} checks passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())






