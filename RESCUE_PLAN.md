# CryBB Maker Bot Rescue Plan

## Current State Analysis

### Authentication Paths

**Current Implementation:**

- **Reads (mentions, lookups)**: OAuth 2.0 Bearer Token (`BEARER_TOKEN`)
- **Tweets & Media**: OAuth 1.0a User Context (`API_KEY`, `API_SECRET`, `ACCESS_TOKEN`, `ACCESS_SECRET`)
- **Bot Identity**: Uses v1.1 `/account/verify_credentials.json` with OAuth 1.0a

**Issues:**

- Mixed authentication (OAuth 2.0 + OAuth 1.0a) creates complexity
- No OAuth 2.0 user context for tweet creation
- Missing `CLIENT_ID`, `CLIENT_SECRET`, `OAUTH2_USER_ACCESS_TOKEN`, `OAUTH2_USER_REFRESH_TOKEN`

### Rate Limits & Backoff

**Current Implementation:**

- Basic rate limit tracking in `TwitterClientV2._rate_limits`
- Simple backoff in `_maybe_sleep()` method
- Adaptive polling in `main.py._calculate_adaptive_wait_time()`

**Issues:**

- No centralized rate limit management
- Missing `x-rate-limit-remaining`, `x-rate-limit-reset` header capture
- No adaptive polling based on remaining requests
- No caching strategy for bot identity (calls API every hour)

### Target Parsing

**Current Implementation:**

- `extract_target_after_bot()` in `utils.py` uses entities-first approach
- Falls back to regex-based extraction
- Properly handles v2 API mention entities

**Status:** ✅ **CORRECT** - Already implements entities-first parsing

### AI Pipeline

**Current Implementation:**

- `Orchestrator.render_with_urls()` enforces `[style_url, pfp_url]` order
- Uses `CRYBB_STYLE_URL` from config
- Proper error handling with fallback to placeholder

**Issues:**

- No URL validation before AI request
- Missing typed errors for bad URLs
- No watermark removal verification

### CRYBB_STYLE_URL Usage

**Current Implementation:**

- Read from `Config.CRYBB_STYLE_URL` environment variable
- Used as first image in `[style_url, pfp_url]` order
- No validation of URL accessibility

**Issues:**

- No HEAD request validation
- No content-type verification

### Tweepy/v1.1 Usage

**Current Implementation:**

- Media upload uses v1.1 endpoint (`upload.twitter.com/1.1/media/upload.json`)
- Bot identity uses v1.1 `/account/verify_credentials.json`
- No Tweepy dependency (uses `requests-oauthlib`)

**Issues:**

- Media upload should use v2 endpoints
- Bot identity should use v2 `/users/me` endpoint

## Implementation Roadmap

### Phase 1: Authentication Modernization

1. **Create `src/auth_v2.py`**

   - `BearerSession`: requests.Session with Bearer token
   - `UserSession`: requests.Session with OAuth 2.0 user context + refresh logic
   - Token store in `~/.crybb/credentials.json` with auto-refresh

2. **Create `src/x_v2.py`**

   - `get_me(session_bearer)` - cached bot identity
   - `get_user_by_username(session_bearer, username)` - cached user lookup
   - `get_mentions(session_bearer, user_id, since_id)` - with expansions
   - `media_upload(session_user_ctx, image_bytes)` - v2 media flow
   - `create_reply(session_user_ctx, text, in_reply_to_tweet_id, media_ids)` - v2 tweets

3. **Update `src/config.py`**
   - Add OAuth 2.0 user context variables
   - Add token URL configuration

### Phase 2: Rate Limiting & Caching

1. **Create `src/ratelimit.py`**

   - Centralized rate limit tracking
   - Adaptive polling with backoff
   - Bot identity caching (1h TTL)
   - User cache (5m TTL)

2. **Update `src/twitter_client_v2.py`**
   - Replace with new v2 implementation
   - Use centralized rate limiting
   - Implement proper caching

### Phase 3: AI Pipeline Hardening

1. **Update `src/ai/nano_banana_client.py`**

   - Add URL validation (HEAD request, content-type check)
   - Add typed errors: `BAD_STYLE_URL`, `BAD_PFP_URL`
   - Ensure no watermark code paths

2. **Update `src/pipeline/orchestrator.py`**
   - Add URL validation before AI calls
   - Improve error handling

### Phase 4: Health & Observability

1. **Update `src/server.py`**
   - Add `/health` endpoint with pipeline status
   - Add `/metrics` endpoint with counters
   - Add failure handling for AI/rate limits

### Phase 5: Diagnostic Tools

1. **Create `tools/oauth2_store_tokens.py`**

   - One-time CLI to store OAuth 2.0 tokens

2. **Update `tools/verify_auth_paths.py`**

   - Test Bearer auth for reads
   - Test OAuth 2.0 user context for v2 media upload
   - Test tweet creation without posting

3. **Update `tools/mentions_probe.py`**

   - Test mentions with expansions
   - Verify target parsing

4. **Update `tools/run_diagnostics.py`**
   - Comprehensive health check
   - All acceptance tests

### Phase 6: Cleanup

1. **Remove v1.1 dependencies**

   - Replace media upload with v2 endpoints
   - Replace bot identity with v2 `/users/me`
   - Remove `requests-oauthlib` dependency

2. **Update `requirements.txt`**
   - Remove unnecessary dependencies
   - Add any missing dependencies

## Endpoints Mapping

### Current Endpoints

- **Reads**: `GET /2/users/{id}/mentions` (Bearer)
- **User Lookup**: `GET /2/users/by/username/{username}` (Bearer)
- **Bot Identity**: `GET /1.1/account/verify_credentials.json` (OAuth 1.0a)
- **Media Upload**: `POST /1.1/media/upload.json` (OAuth 1.0a)
- **Tweet Creation**: `POST /2/tweets` (OAuth 1.0a)

### Target Endpoints

- **Reads**: `GET /2/users/{id}/mentions` (Bearer)
- **User Lookup**: `GET /2/users/by/username/{username}` (Bearer)
- **Bot Identity**: `GET /2/users/me` (Bearer) - cached 1h
- **Media Upload**: `POST /2/media/upload` (INIT) → `POST /2/media/upload/append` → `POST /2/media/upload/finalize` (OAuth 2.0 user context)
- **Tweet Creation**: `POST /2/tweets` (OAuth 2.0 user context)

## Environment Variables

### Current Required

```
BEARER_TOKEN=
API_KEY=
API_SECRET=
ACCESS_TOKEN=
ACCESS_SECRET=
CLIENT_ID=
CLIENT_SECRET=
REPLICATE_API_TOKEN=
CRYBB_STYLE_URL=
```

### Additional Required

```
OAUTH2_USER_ACCESS_TOKEN=
OAUTH2_USER_REFRESH_TOKEN=
OAUTH2_TOKEN_URL=https://api.twitter.com/2/oauth2/token
```

## Acceptance Criteria

1. **AI Smoke Test**: `python tools/run_ai_smoke.py --pfp-url <url>` PASS
2. **Auth Verification**: `python tools/verify_auth_paths.py` PASS
3. **Mentions Probe**: `python tools/mentions_probe.py` shows correct targets
4. **Diagnostics**: `python tools/run_diagnostics.py` all PASS
5. **Local Bot**: `python -m src.main` runs without immediate rate limits
6. **Production Ready**: Service runs on droplet with systemd

## Risk Mitigation

1. **Gradual Migration**: Keep existing code working while implementing new components
2. **Comprehensive Testing**: Each phase includes diagnostic tools
3. **Fallback Mechanisms**: AI failures fall back to placeholder images
4. **Rate Limit Safety**: Conservative polling with exponential backoff
5. **Token Management**: Secure storage and auto-refresh for OAuth 2.0 tokens

## Timeline

- **Phase 1-2**: Authentication & Rate Limiting (Core infrastructure)
- **Phase 3**: AI Pipeline Hardening (Reliability)
- **Phase 4**: Health & Observability (Production readiness)
- **Phase 5**: Diagnostic Tools (Testing & validation)
- **Phase 6**: Cleanup (Final polish)

Total estimated time: 2-3 hours for complete implementation and testing.

