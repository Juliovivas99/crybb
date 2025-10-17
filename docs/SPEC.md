### CryBB Bot — Product & Behavior Spec

- Summary: A Twitter/X bot that polls mentions, resolves a target username explicitly mentioned after the bot, generates a CryBB-style PFP (AI or placeholder), and replies with an image. Reads are via Bearer; writes (media upload v1.1 and tweet creation v2) are via OAuth1a. The bot advances since_id only after a contiguous prefix of successful mention processing and persists processed IDs.

### Decision Tree

```mermaid
flowchart TD
  A[New mention fetched] --> B{Author verified?}
  B -- No --> Z[Skip]
  B -- Yes --> C{Explicit @bot @username?}
  C -- No --> Z2[Skip]
  C -- Yes --> D[Resolve target user (batch→cache→network)]
  D --> E{Overlay keyword + attached image?}
  E -- Yes --> F[Overlay render bottom-left]:::missing
  E -- No --> G[Generate (AI or placeholder)]
  G --> H[Reply with image]
  classDef missing fill:#ffe0e0,stroke:#ff9999,color:#333;
```

Notes from code:

- Processing and reply path (image):

```176:186:/Users/juliovivas/Vscode/crybb/src/main.py
# Reply with processed image
reply_text = f"Welcome to $CRYBB @{target_username} 🍼\n\nNO CRYING IN THE CASINO."
self.twitter_client.reply_with_image(tweet_id, reply_text, image_bytes)

# Update metrics
from server import update_metrics
update_metrics(processed=1, replies_sent=1, last_mention_time=tweet_data.get('created_at'))
```

- Fallback text-only on failure (batch loop):

```312:321:/Users/juliovivas/Vscode/crybb/src/main.py
            try:
                self.twitter_client.create_reply_text(
                    in_reply_to=tid,
                    text="Sorry — I couldn't render that one. Try again in a bit! 💛"
                )
                self.storage.mark_processed(tid)
                success_ids.add(tid)
                print(f"📝 Sent fallback text for {tid}")
```

- Overlay mode: not implemented (no references in `src/` to `assets/overlays/*`).

### Inputs & Outputs

- Input: Mentions v2 with expansions (includes.users) via Bearer.

```204:214:/Users/juliovivas/Vscode/crybb/src/x_v2.py
def get_mentions(self, user_id: str, since_id: Optional[str] = None,
                max_results: int = 100) -> List[Dict[str, Any]] | Dict[str, Any]:
    """Get mentions with comprehensive expansions."""
    try:
        url = f"{self.base_url}/users/{user_id}/mentions"
        params = {
            'max_results': max_results,
            'expansions': 'author_id,entities.mentions.username',
```

- Outputs: media upload v1.1 (OAuth1a), then create reply (v2, OAuth1a-signed), or combined reply helper.

```309:316:/Users/juliovivas/Vscode/crybb/src/x_v2.py
url = "https://upload.twitter.com/1.1/media/upload.json"
files = {"media": ("crybb.jpg", image_bytes, mime)}

# Use OAuth1a for v1.1 media upload endpoint
resp = requests.post(url, files=files, auth=self._oauth1(), timeout=30)
self._capture_rate_limits(resp, 'media/upload')
self._log_request('OAuth1a', 'POST', url, resp.status_code, 'media/upload')
```

```337:345:/Users/juliovivas/Vscode/crybb/src/x_v2.py
url = f"{self.base_url}/tweets"
data = {
    'text': text,
    'reply': {
        'in_reply_to_tweet_id': in_reply_to_tweet_id
    }
}
```

### Idempotency / Queue Semantics

- Processed IDs persistence and checks:

```55:63:/Users/juliovivas/Vscode/crybb/src/storage.py
def mark_processed(self, tweet_id: str) -> None:
    """Atomically mark a tweet as processed."""
    try:
        os.makedirs(os.path.dirname(self.processed_ids_file), exist_ok=True)
        current = self.read_processed_ids()
        if tweet_id in current:
            return
```

- Contiguous since_id advancement after successes (batch prefix):

```326:333:/Users/juliovivas/Vscode/crybb/src/main.py
# Advance since_id only to last *contiguous* success from the oldest.
prefix_last = last_contiguous_success(oldest_first)
if prefix_last:
    prev = self.storage.read_since_id()
    if prefix_last != prev:
        self.storage.write_since_id(prefix_last)
        print(f"📝 since_id → {prefix_last}")
```

### Limits and Rate Limiting

- Per-author limiter (sliding window, default 12/h via Config) with whitelist bypass:

```20:25:/Users/juliovivas/Vscode/crybb/src/rate_limiter.py
def allow(self, author_id: str) -> bool:
    """Check if user is allowed to make a request."""
    # Whitelist bypass for incoming mentions
    if str(author_id).lower() in Config.WHITELIST_HANDLES:
        return True  # Whitelisted users can call the bot without restriction
```

- Per-target limiter (no whitelist bypass, default 5/h via Config):

```23:33:/Users/juliovivas/Vscode/crybb/src/per_user_limiter.py
def allow(self, username: str) -> bool:
    user_key = normalize(username)
    # No whitelist bypass - all users treated equally for outgoing replies

    now = time.time()
    self._prune(user_key, now)
    dq = self.user_to_timestamps[user_key]
    if len(dq) < self.limit:
        dq.append(now)
        return True
    return False
```

- Bearer reads vs OAuth1a writes and RL capture/sleep:

```92:100:/Users/juliovivas/Vscode/crybb/src/x_v2.py
def _capture_rate_limits(self, response: requests.Response, endpoint: str) -> None:
    """Capture rate limit information from response headers."""
    try:
        limit = int(response.headers.get('x-rate-limit-limit', 0))
        remaining = int(response.headers.get('x-rate-limit-remaining', 0))
        reset = int(response.headers.get('x-rate-limit-reset', 0))
```

```125:133:/Users/juliovivas/Vscode/crybb/src/x_v2.py
def maybe_sleep(self, endpoint: str, min_remaining: int = 2) -> None:
    if endpoint not in self._rate_limits:
        return
    rate_info = self._rate_limits[endpoint]
    if rate_info.remaining < min_remaining:
        now = time.time()
        wait = max(0.0, rate_info.reset - now) + 5.0
```

### Caching and Batch Snapshot

- Bot identity cached (OAuth1a verify credentials):

```135:143:/Users/juliovivas/Vscode/crybb/src/x_v2.py
def get_me(self) -> Tuple[str, str]:
    """Get bot identity with indefinite caching."""
    # Return cached if available
    if self._bot_identity:
        return self._bot_identity

    try:
        url = "https://api.twitter.com/1.1/account/verify_credentials.json"
```

- User cache TTL 5 minutes and lookup by username:

```66:70:/Users/juliovivas/Vscode/crybb/src/x_v2.py
# Caching
self._bot_identity: Optional[Tuple[str, str]] = None
self._bot_identity_fetched_at: Optional[float] = None
self._user_cache: Dict[str, UserInfo] = {}
self._user_cache_ttl = 300  # 5 minutes
```

- Batch snapshot and context usage:

```23:31:/Users/juliovivas/Vscode/crybb/src/batch_context.py
def get_user(self, username_lc: str) -> Dict[str, Any] | None:
    """Get user data from batch snapshot or inflight pins."""
    now = time.time()

    # 1) Check batch snapshot first
    u = self.batch_users.get(username_lc)
    if u:
```

### Error Handling

- Mentions 429: sleep to reset and return rate-limited marker:

```223:231:/Users/juliovivas/Vscode/crybb/src/x_v2.py
if response.status_code == 429:
    # Rate limited: sleep until reset + 5s and return marker
    rate = self._rate_limits.get('users/mentions')
    if rate:
        now = time.time()
        wait = max(0.0, rate.reset - now) + 5.0
        print(f"Mentions rate-limited; sleeping {wait:.1f}s until reset+5s")
        time.sleep(wait)
```

- Per-mention error handling with error reply and metrics:

```191:199:/Users/juliovivas/Vscode/crybb/src/main.py
except Exception as e:
    print(f"Error processing mention {tweet_data.get('id', 'unknown')}: {e}")
    try:
        self.twitter_client.reply_with_image(
            tweet_data.get('id', ''),
            format_error_message(),
            self._create_error_image()
        )
```

### Required Environment Variables

- Credentials and pipeline requirements (validated at import unless SKIP_CONFIG_VALIDATION is set):

```62:71:/Users/juliovivas/Vscode/crybb/src/config.py
required_creds = [
    ("CLIENT_ID", cls.CLIENT_ID),
    ("CLIENT_SECRET", cls.CLIENT_SECRET),
    ("API_KEY", cls.API_KEY),
    ("API_SECRET", cls.API_SECRET),
    ("ACCESS_TOKEN", cls.ACCESS_TOKEN),
    ("ACCESS_SECRET", cls.ACCESS_SECRET),
    ("BEARER_TOKEN", cls.BEARER_TOKEN),
]
```

```79:87:/Users/juliovivas/Vscode/crybb/src/config.py
if (cls.IMAGE_PIPELINE or "ai").lower() == "ai":
    ai_missing = []
    if not cls.REPLICATE_API_TOKEN:
        ai_missing.append("REPLICATE_API_TOKEN")
    if not cls.CRYBB_STYLE_URL:
        ai_missing.append("CRYBB_STYLE_URL")
    if ai_missing:
        raise ValueError(
            "IMAGE_PIPELINE=ai requires: " + ", ".join(ai_missing)
        )
```

### Explicitly Not Implemented (per code)

- Overlay mode: Not implemented. No `src/` code references overlay assets or placement helpers; only placeholder rendering exists.
