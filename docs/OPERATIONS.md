### CryBB — Operations Guide

### Environment Variables (from src/config.py and env.example)

| Name                         | Required? | Default                   | Purpose                          |
| ---------------------------- | --------- | ------------------------- | -------------------------------- | ------ | ---- |
| CLIENT_ID                    | Yes       | ""                        | OAuth client id                  |
| CLIENT_SECRET                | Yes       | ""                        | OAuth client secret              |
| API_KEY                      | Yes       | ""                        | OAuth1a key                      |
| API_SECRET                   | Yes       | ""                        | OAuth1a secret                   |
| ACCESS_TOKEN                 | Yes       | ""                        | OAuth1a access token             |
| ACCESS_SECRET                | Yes       | ""                        | OAuth1a access secret            |
| BEARER_TOKEN                 | Yes       | ""                        | OAuth2 Bearer (reads)            |
| BOT_HANDLE                   | No        | crybbmaker                | Bot handle                       |
| PORT                         | No        | 8000                      | Health server port               |
| TWITTER_MODE                 | No        | live                      | live                             | dryrun | mock |
| OUTBOX_DIR                   | No        | outbox                    | Local storage/dryrun outbox      |
| FIXTURES_DIR                 | No        | fixtures                  | Test fixtures                    |
| REPLICATE_API_TOKEN          | Yes if ai | ""                        | Replicate token                  |
| REPLICATE_MODEL              | No        | google/nano-banana        | AI model/version                 |
| REPLICATE_TIMEOUT_SECS       | No        | 120                       | AI timeout seconds               |
| REPLICATE_POLL_INTERVAL_SECS | No        | 2                         | AI polling interval              |
| AI_MAX_CONCURRENCY           | No        | 2                         | AI concurrency                   |
| AI_MAX_ATTEMPTS              | No        | 2                         | AI retries                       |
| CRYBB_STYLE_URL              | Yes if ai | (none)                    | Style image URL                  |
| IMAGE_PIPELINE               | No        | ai                        | ai or placeholder                |
| WHITELIST_HANDLES            | No        | thenighguy,crybaby_on_sol | Per-author bypass (incoming)     |
| PER_USER_HOURLY_LIMIT        | No        | 12                        | Per-author hourly cap            |
| PER_TARGET_HOURLY_LIMIT      | No        | 5                         | Per-target hourly cap            |
| AWAKE_MIN_SECS               | No        | 180                       | Awake poll min                   |
| AWAKE_MAX_SECS               | No        | 300                       | Awake poll max                   |
| SLEEPER_MIN_SECS             | No        | 600                       | Sleeper hint (not directly used) |
| RT_LIKE_THRESHOLD            | No        | 10                        | Sleeper RT threshold             |

Validation references:

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

### Local Startup

```bash
python -m src.main
```

Health server starts in a background thread on `:8000` (uvicorn). See `src/server.py` and main startup.

### Systemd (droplet)

Service unit in `scripts/crybb-bot.service`.

```bash
sudo systemctl daemon-reload
sudo systemctl enable crybb-bot
sudo systemctl restart crybb-bot
sudo systemctl status crybb-bot
journalctl -u crybb-bot -f
```

### Health & Metrics

- Endpoints:

```23:31:/Users/juliovivas/Vscode/crybb/src/server.py
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "ok": True,
        "timestamp": datetime.utcnow().isoformat(),
```

```36:46:/Users/juliovivas/Vscode/crybb/src/server.py
@app.get("/metrics")
async def get_metrics():
    """Metrics endpoint with counters and status."""
    return {
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "counters": {
            "processed": metrics["processed"],
            "ai_fail": metrics["ai_fail"],
```

### Incidents & Remediation

- Writes 401/403: check OAuth1a creds; writes occur in media upload and tweet create:

```309:316:/Users/juliovivas/Vscode/crybb/src/x_v2.py
resp = requests.post(url, files=files, auth=self._oauth1(), timeout=30)
self._capture_rate_limits(resp, 'media/upload')
self._log_request('OAuth1a', 'POST', url, resp.status_code, 'media/upload')
```

```350:353:/Users/juliovivas/Vscode/crybb/src/x_v2.py
response = requests.post(url, json=data, auth=self._oauth1(), timeout=30)
self._capture_rate_limits(response, 'tweets')
self._log_request('OAuth1a', 'POST', url, response.status_code, 'tweets')
```

- Mentions 429: client sleeps until reset+5s and returns marker:

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

- Image pipeline errors: per-mention handler attempts error reply; batch fallback can send text-only and mark processed (see SPEC quotes from `src/main.py`).

### Deploy Checklist

```bash
git pull
sudo systemctl restart crybb-bot
journalctl -u crybb-bot -f
curl -s localhost:8000/health | jq .
```

### Storage & Safe Resets

- Files:
  - `outbox/since_id.json`: advanced to last contiguous success (see main contiguous advancement).
  - `outbox/processed_ids.json`: all processed IDs (`src/storage.py`).
- Reset options:
  - Reprocess a tweet: remove its ID from `processed_ids.json`.
  - Reset polling: delete `since_id.json` (bot resumes using API defaults).
