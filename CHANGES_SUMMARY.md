# CryBB Bot - Fix Summary

## Changes Applied

### 1. **src/utils.py**

- ✅ Added `extract_target_after_bot()` - Robust target extraction using Twitter v2 entities
- ✅ Added `normalize_pfp_url()` - Upgrades profile images to 400x400 resolution
- ✅ Updated `format_friendly_message()` - Changed emoji to 🍼

**Key Feature**: Extracts first username mentioned immediately after @crybbmaker in tweet entities

### 2. **src/twitter_client_live.py**

- ✅ Added `import io` for BytesIO support
- ✅ Fixed `get_mentions()` - Changed `tweet.fields` to `tweet_fields` (snake_case)
- ✅ Added expansions: `["author_id", "entities.mentions.username"]`
- ✅ Fixed `reply_with_image()` - Wraps bytes in `io.BytesIO()` before upload
- ✅ Added logging for media upload size

**Key Fix**: Resolves "'bytes' object has no attribute 'tell'" error

### 3. **src/pipeline/orchestrator.py**

- ✅ Added `from typing import List` import
- ✅ Added `render_with_urls()` method - Accepts list of image URLs
- ✅ Enforced image order: `[CRYBB_STYLE_URL, TARGET_PFP_URL]`
- ✅ Added logging to show nano-banana image order

**Key Feature**: First image is style anchor, second is target's profile picture

### 4. **src/main.py**

- ✅ Updated imports to use new utility functions
- ✅ Implemented robust target extraction with `extract_target_after_bot()`
- ✅ Added author username fallback logic
- ✅ Integrated `normalize_pfp_url()` for higher resolution images
- ✅ Updated to use `orchestrator.render_with_urls()` with proper image order
- ✅ Added exponential backoff for rate limits (429 errors)
- ✅ Improved logging for target selection and PFP URLs

**Key Feature**: Properly handles @crybbmaker @target mentions with fallback to author

### 5. **src/config.py**

- ✅ Changed default `POLL_SECONDS` from `15` to `60`

**Key Feature**: Reduces API calls and rate limit pressure

## Expected Behavior

### Mention Processing Flow:

1. User tweets: `@crybbmaker @juliovivas99 make me #crybb`
2. Bot detects mention
3. Extracts `@juliovivas99` as target (first username after @crybbmaker)
4. Fetches `@juliovivas99`'s profile image (400x400 resolution)
5. Calls nano-banana with:
   - Image 1 (style): CRYBB_STYLE_URL
   - Image 2 (content): juliovivas99's profile picture
6. Replies in thread with generated image: "Here's your CryBB PFP @juliovivas99 🍼"

### Fallback Logic:

- If no username after @crybbmaker → uses first non-bot mention
- If no mentions at all → uses tweet author's username
- If user lookup fails → sends error image

### Error Fixes:

- ❌ ~~`Unexpected parameter: tweet.fields`~~ → ✅ Fixed with `tweet_fields`
- ❌ ~~`'bytes' object has no attribute 'tell'`~~ → ✅ Fixed with `io.BytesIO()`
- ❌ ~~Rate limit 429 errors~~ → ✅ Added exponential backoff

## Deployment Steps

### 1. Commit and Push Changes:

```bash
cd /Users/juliovivas/Vscode/crybb
git add .
git commit -m "Fix bot mention processing, image upload, and API params"
git push origin main
```

### 2. Deploy to Droplet:

```bash
ssh root@138.197.3.144
cd /opt/crybb-bot
git pull
sudo systemctl restart crybb-bot
journalctl -u crybb-bot -f
```

### 3. Verify Logs:

Expected output:

```
✅ No more "Unexpected parameter: tweet.fields"
✅ "Target chosen: @juliovivas99"
✅ "PFP=https://pbs.twimg.com/profile_images/.../_400x400.jpg"
✅ "Nano-banana image order: [0]=CRYBB_STYLE_URL, [1]=TARGET_PFP_URL"
✅ "Uploading media: 45678 bytes"
✅ "Successfully replied to tweet 1234567890"
```

## Testing

### Test Command:

Tweet: `@crybbmaker @target_username make me #crybb`

### Expected Result:

Bot replies with AI-generated image using:

- Style: Your CRYBB_STYLE_URL constant
- Content: Target user's profile picture

## Files Modified:

- ✅ src/utils.py
- ✅ src/twitter_client_live.py
- ✅ src/pipeline/orchestrator.py
- ✅ src/main.py
- ✅ src/config.py

## Configuration:

- ✅ POLL_SECONDS=30 (default, can be overridden in .env)

All changes complete and ready for deployment! 🚀
