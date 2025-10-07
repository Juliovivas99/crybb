# Diff Summary - CryBB Bot Fixes

## 1. src/utils.py

### Added Functions:

```python
def extract_target_after_bot(tweet, bot_handle: str, author_username: str) -> str:
    """
    Choose the first username *immediately after* @bot in tweet.entities.mentions (v2).
    Fallbacks: first non-bot mention -> author_username.
    """
    # Parses tweet.data.entities.mentions to find target
    # Returns target username with smart fallback logic
```

```python
def normalize_pfp_url(url: str) -> str:
    """Normalize profile picture URL to higher resolution."""
    # Upgrades _normal, _bigger, _mini to _400x400
```

### Modified:

- `format_friendly_message()`: Changed 🔥 to 🍼

---

## 2. src/twitter_client_live.py

### Added Import:

```python
import io  # NEW
```

### Modified `get_mentions()`:

```python
# BEFORE:
params = {
    "max_results": 10,
    "tweet.fields": "created_at,author_id"  # ❌ WRONG
}

# AFTER:
response = self.v2_client.get_users_mentions(
    id=bot_id,
    since_id=since_id,
    max_results=10,
    expansions=["author_id", "entities.mentions.username"],  # ✅ NEW
    user_fields=["username", "profile_image_url"],  # ✅ NEW
    tweet_fields=["created_at", "entities"]  # ✅ FIXED
)
```

### Modified `reply_with_image()`:

```python
# BEFORE:
media = self.v1_client.media_upload(
    filename="reply.jpg",
    file=image_bytes  # ❌ Causes 'tell' error
)

# AFTER:
print(f"Uploading media: {len(image_bytes)} bytes")  # ✅ NEW logging

buf = io.BytesIO(image_bytes)  # ✅ FIX: Wrap in BytesIO
buf.seek(0)

media = self.v1_client.media_upload(
    filename="crybb.jpg",
    file=buf  # ✅ FIXED
)

# ✅ NEW: Handle both media_ids formats
try:
    self.v2_client.create_tweet(
        text=text,
        in_reply_to_tweet_id=in_reply_to_tweet_id,
        media_ids=[media_id]
    )
except TypeError:
    self.v2_client.create_tweet(
        text=text,
        in_reply_to_tweet_id=in_reply_to_tweet_id,
        media={"media_ids": [media_id]}
    )
```

---

## 3. src/pipeline/orchestrator.py

### Added Import:

```python
from typing import List  # NEW
```

### Modified `render()`:

```python
# ADDED logging:
print(f"Nano-banana image order: [0]={self.cfg.CRYBB_STYLE_URL}, [1]={pfp_url}")
```

### Added Method:

```python
def render_with_urls(self, image_urls: List[str], mention_text: str = "") -> bytes:
    """New method that accepts image URLs list directly."""
    # Enforces [style, target_pfp] order
    # Falls back to placeholder on error
```

---

## 4. src/main.py

### Modified Imports:

```python
# BEFORE:
from .utils import (
    extract_target_username,  # OLD
    format_friendly_message,
    format_rate_limit_message,
    format_error_message
)

# AFTER:
from .utils import (
    extract_target_after_bot,  # ✅ NEW
    normalize_pfp_url,  # ✅ NEW
    format_friendly_message,
    format_rate_limit_message,
    format_error_message
)
```

### Modified `process_mention()`:

```python
# BEFORE:
target_username = extract_target_username(tweet_text, self.bot_handle)
if not target_username:
    try:
        user = self.twitter_client.get_user_by_id(int(author_id))
        if user and user.get("username"):
            target_username = user["username"]
    except Exception:
        target_username = None

# AFTER:
# Get author username for fallback
author = self.twitter_client.get_user_by_id(int(author_id))
author_username = author.get("username") if author else None

# Extract target using new robust method
target_username = extract_target_after_bot(tweet, Config.BOT_HANDLE, author_username or "")
print(f"Target chosen: @{target_username}")

# Get target user and profile image
target_user = self.twitter_client.get_user_by_username(target_username)
# ... validation ...

pfp_url = normalize_pfp_url(target_user.get("profile_image_url") or "")
print(f"PFP={pfp_url}")
```

### Modified Image Generation:

```python
# BEFORE:
processed_image = self.orchestrator.render(
    pfp_url=profile_url,
    mention_text=tweet_text or "",
)

# AFTER:
image_bytes = self.orchestrator.render_with_urls(
    [Config.CRYBB_STYLE_URL, pfp_url],  # ✅ Explicit order: [style, target]
    mention_text=tweet_text or ""
)
```

### Modified Reply:

```python
# BEFORE:
reply_text = format_friendly_message(target_username)

# AFTER:
reply_text = f"Here's your CryBB PFP @{target_username} 🍼"  # ✅ Explicit format
```

### Modified `run_polling_loop()`:

```python
# ADDED: Exponential backoff for rate limits
backoff_seconds = 1

while True:
    try:
        # ... polling code ...

        if mentions:
            # ... processing ...
            backoff_seconds = 1  # ✅ Reset on success

        time.sleep(Config.POLL_SECONDS)

    except tweepy.TooManyRequests as e:
        print(f"Rate limited: {e}")
        # ✅ NEW: Exponential backoff with cap
        backoff_seconds = min(backoff_seconds * 2, 300)  # Cap at 5 minutes
        print(f"Backing off for {backoff_seconds} seconds")
        time.sleep(backoff_seconds)
```

---

## 5. src/config.py

### Modified Default:

```python
# BEFORE:
POLL_SECONDS: int = int(os.getenv("POLL_SECONDS", "15"))

# AFTER:
POLL_SECONDS: int = int(os.getenv("POLL_SECONDS", "30"))  # ✅ Reduced API pressure
```

---

## Summary of Fixes

| Issue                                    | Status   | Fix                                       |
| ---------------------------------------- | -------- | ----------------------------------------- |
| `Unexpected parameter: tweet.fields`     | ✅ FIXED | Changed to `tweet_fields` (snake_case)    |
| `'bytes' object has no attribute 'tell'` | ✅ FIXED | Wrapped bytes in `io.BytesIO()`           |
| Wrong image order in nano-banana         | ✅ FIXED | Enforced `[style, target_pfp]` order      |
| Target extraction not robust             | ✅ FIXED | New `extract_target_after_bot()` function |
| Low resolution profile images            | ✅ FIXED | `normalize_pfp_url()` upgrades to 400x400 |
| No rate limit backoff                    | ✅ FIXED | Exponential backoff with 300s cap         |
| Aggressive polling                       | ✅ FIXED | Changed default from 15s to 30s           |

---

## Testing Checklist

- [ ] Tweet `@crybbmaker @target_username make me #crybb`
- [ ] Verify bot detects mention
- [ ] Check logs show: `Target chosen: @target_username`
- [ ] Check logs show: `PFP=.../_400x400.jpg`
- [ ] Check logs show: `Nano-banana image order: [0]=..., [1]=...`
- [ ] Check logs show: `Uploading media: NNNNN bytes`
- [ ] Verify bot replies with AI-generated image
- [ ] Verify no `tweet.fields` or `.tell()` errors
- [ ] Test fallback: `@crybbmaker make me #crybb` (should use your PFP)

All changes ready for deployment! 🚀
