### CryBB Docs Index

- SPEC: docs/SPEC.md
- ARCHITECTURE: docs/ARCHITECTURE.md
- OPERATIONS: docs/OPERATIONS.md

### At a Glance

- Endpoints & Auth

  - GET /users/:id/mentions (v2, Bearer) — `src/x_v2.py`
  - POST /1.1/media/upload.json (v1.1, OAuth1a) — `src/x_v2.py`
  - POST /2/tweets (v2, OAuth1a) — `src/x_v2.py`
  - GET /1.1/account/verify_credentials.json (OAuth1a) — `src/x_v2.py`
  - GET /2/users/:id/tweets (v2, Bearer) — `src/x_v2.py`
  - POST /1.1/statuses/retweet/:id.json (v1.1, OAuth1a) — `src/x_v2.py`

- Polling Cadence

  - Awake random: AWAKE_MIN_SECS–AWAKE_MAX_SECS (config-driven)
  - Sleeper random: ~480–600s (quiet periods)
  - Mentions 429: until reset+5s (client-enforced)

- Key Limits

  - Per-author sliding window + whitelist bypass: `src/rate_limiter.py` (default 12/h)
  - Per-target limiter (no whitelist bypass): `src/per_user_limiter.py` (default 5/h)
  - Sleeper RT threshold: `RT_LIKE_THRESHOLD` (config)

- Storage Files

  - `outbox/since_id.json` — contiguous advancement
  - `outbox/processed_ids.json` — processed ID set

- Not Implemented
  - Overlay mode (assets/overlays/\*) — no active code references in `src/`
