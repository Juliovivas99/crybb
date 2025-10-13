# Repository Inventory & Lean-Down Plan

Generated: /Users/juliovivas/Vscode/crybb

## Project Overview
- **Python Version**: 3.8+
- **Package Layout**: src/ + tools/ + tests/
- **Runtime Modes**: mock, dryrun, live
- **Image Pipeline**: ai (with placeholder fallback)

## File Inventory

| Path | Size (KB) | Type | Purpose | Role | Flags |
|------|-----------|------|---------|------|-------|
| .dockerignore.suggested | 0.1 | suggested | # Suggested .dockerignore | unknown | - |
| .env | 1.42 | unknown | # OAuth 2.0 user context | unknown | - |
| .env.example.min | 0.36 | min | Unknown purpose | unknown | - |
| .env.local.tokens | 0.3 | tokens | # OAuth 2.0 User Tokens | unknown | - |
| CHANGES_SUMMARY.md | 3.93 | md | Documentation | docs | - |
| DEPLOYMENT_GUIDE.md | 7.83 | md | Documentation | docs | - |
| DIFF_SUMMARY.md | 6.56 | md | Documentation | docs | - |
| DIGITALOCEAN_DEPLOYMENT.md | 4.95 | md | Documentation | docs | - |
| LIVE_TESTING_SETUP.md | 4.3 | md | Documentation | docs | - |
| MENTION_HANDLING_SUMMARY.md | 7.75 | md | Documentation | docs | - |
| Makefile | 0.61 | unknown | Build automation | config | - |
| README.md | 11.09 | md | Project documentation | docs | - |
| REFACTOR_SUMMARY.md | 6.3 | md | Documentation | docs | - |
| RESCUE_PLAN.md | 6.92 | md | Documentation | docs | - |
| RESCUE_RESULT.md | 6.57 | md | Documentation | docs | - |
| TWITTER_V2_MIGRATION.md | 6.77 | md | Documentation | docs | - |
| assets/crybb.jpeg | 38.3 | jpeg | Asset file | asset | - |
| debug_mentions.py | 0.6 | py | #!/usr/bin/env python3 | unknown | DEAD |
| env.example | 0.81 | example | # OAuth 1.0a credentials (required for media upload v1.1 endpoint) | unknown | - |
| fixtures/mentions.json | 0.13 | json | Test fixture | asset | - |
| fixtures/users.json | 0.29 | json | Test fixture | asset | - |
| requirements.txt | 0.14 | txt | Python dependencies | config | - |
| reset_since_id.py | 0.59 | py | #!/usr/bin/env python3 | unknown | DEAD |
| scripts/crybb-bot.service | 0.99 | service | Unknown purpose | unknown | - |
| scripts/deploy.sh | 2.75 | sh | #!/usr/bin/env bash | unknown | - |
| scripts/deploy_complete.sh | 10.21 | sh | #!/usr/bin/env bash | unknown | - |
| scripts/deployment_summary.sh | 2.29 | sh | #!/usr/bin/env bash | unknown | - |
| scripts/harden.sh | 2.0 | sh | #!/usr/bin/env bash | unknown | - |
| scripts/harden_complete.sh | 6.83 | sh | #!/usr/bin/env bash | unknown | - |
| scripts/test_health.sh | 0.48 | sh | #!/usr/bin/env bash | unknown | - |
| scripts/update.sh | 0.72 | sh | #!/usr/bin/env bash | unknown | - |
| src/__init__.py | 0.09 | py | """ | runtime | - |
| src/ai/nano_banana_client.py | 4.65 | py | AI pipeline module | runtime | DEAD |
| src/ai/prompt_crybb.py | 0.45 | py | AI pipeline module | runtime | - |
| src/auth_v2.py | 6.85 | py | """ | runtime | DEAD |
| src/config.py | 3.81 | py | Configuration management | runtime | - |
| src/image_processor.py | 1.24 | py | """ | runtime | - |
| src/main.py | 14.18 | py | Main application entry point | runtime | ENTRYPOINT |
| src/per_user_limiter.py | 1.18 | py | Unknown purpose | runtime | DEAD |
| src/pipeline/orchestrator.py | 2.97 | py | Image processing orchestration | runtime | - |
| src/rate_limiter.py | 2.44 | py | """ | runtime | - |
| src/ratelimit.py | 5.26 | py | """ | runtime | DEAD |
| src/retry.py | 2.29 | py | """ | runtime | DEAD |
| src/server.py | 2.48 | py | Health/metrics server | runtime | ENTRYPOINT |
| src/storage.py | 1.14 | py | """ | runtime | DEAD |
| src/twitter_client_dryrun_v2.py | 5.38 | py | Twitter/X API client | runtime | DEAD |
| src/twitter_client_mock_v2.py | 5.51 | py | Twitter/X API client | runtime | DEAD |
| src/twitter_client_v2.py | 25.14 | py | Twitter/X API client | runtime | - |
| src/twitter_client_v2_new.py | 5.53 | py | Twitter/X API client | runtime | DEAD |
| src/twitter_factory.py | 0.84 | py | Twitter/X API client | runtime | - |
| src/utils.py | 3.27 | py | """ | runtime | - |
| src/x_v2.py | 15.85 | py | """ | runtime | DEAD |
| test_auth.py | 1.37 | py | #!/usr/bin/env python3 | unknown | ENTRYPOINT |
| test_mentions.py | 0.79 | py | #!/usr/bin/env python3 | unknown | ENTRYPOINT |
| tools/_audit_utils.py | 9.71 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/_diag_lib.py | 3.95 | py | Development tool/diagnostics | dev-tool | - |
| tools/diagnose_v2.py | 8.98 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/mentions_probe.py | 5.93 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/oauth2_pkce_callback_server.py | 12.82 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/oauth2_store_tokens.py | 1.69 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/probe_x_api.py | 7.23 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/repo_audit.py | 16.16 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/run_ai_smoke.py | 1.12 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/run_diagnostics.py | 15.88 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/simulate_once.py | 2.29 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/sleeper_probe.py | 0.71 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_basic_api.py | 7.69 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_basic_plan.py | 7.53 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_end_to_end_no_post.py | 4.42 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_media_upload.py | 2.26 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_mention_parsing.py | 7.81 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_per_user_limiter.py | 0.93 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/verify_auth_paths.py | 7.05 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |

## Dependencies Analysis

### Unused Dependencies

- Pillow
- python-dotenv
- requests-oauthlib>=1.3.1

## Environment Variables

### Used Variables
- ACCESS_SECRET
- ACCESS_TOKEN
- AI_MAX_ATTEMPTS
- AI_MAX_CONCURRENCY
- API_KEY
- API_SECRET
- AWAKE_MAX_SECS
- AWAKE_MIN_SECS
- BEARER_TOKEN
- BOT_HANDLE
- CLIENT_ID
- CLIENT_SECRET
- CRYBB_STYLE_URL
- FIXTURES_DIR
- HTTP_TIMEOUT_SECS
- IMAGE_PIPELINE
- OUTBOX_DIR
- PER_USER_HOURLY_LIMIT
- POLL_SECONDS
- PORT
- REPLICATE_API_TOKEN
- REPLICATE_MODEL
- REPLICATE_POLL_INTERVAL_SECS
- REPLICATE_TIMEOUT_SECS
- RT_LIKE_THRESHOLD
- SKIP_CONFIG_VALIDATION
- SLEEPER_MIN_SECS
- TWITTER_MODE
- WHITELIST_HANDLES

## Lean-Down Proposal

| Action | Path | Reason |
|--------|------|--------|
| Remove | debug_mentions.py | Unused module - no imports or entrypoint |
| Remove | reset_since_id.py | Unused module - no imports or entrypoint |
| Remove | src/x_v2.py | Unused module - no imports or entrypoint |
| Remove | src/twitter_client_dryrun_v2.py | Unused module - no imports or entrypoint |
| Remove | src/per_user_limiter.py | Unused module - no imports or entrypoint |
| Remove | src/ratelimit.py | Unused module - no imports or entrypoint |
| Remove | src/retry.py | Unused module - no imports or entrypoint |
| Remove | src/auth_v2.py | Unused module - no imports or entrypoint |
| Remove | src/twitter_client_v2_new.py | Unused module - no imports or entrypoint |
| Remove | src/storage.py | Unused module - no imports or entrypoint |
| Remove | src/twitter_client_mock_v2.py | Unused module - no imports or entrypoint |
| Remove | src/ai/nano_banana_client.py | Unused module - no imports or entrypoint |

## Next Actions

### Commands to Execute

```bash
git rm debug_mentions.py
```

```bash
git rm reset_since_id.py
```

```bash
git rm src/x_v2.py
```

```bash
git rm src/twitter_client_dryrun_v2.py
```

```bash
git rm src/per_user_limiter.py
```

```bash
git rm src/ratelimit.py
```

```bash
git rm src/retry.py
```

```bash
git rm src/auth_v2.py
```

```bash
git rm src/twitter_client_v2_new.py
```

```bash
git rm src/storage.py
```

```bash
git rm src/twitter_client_mock_v2.py
```

```bash
git rm src/ai/nano_banana_client.py
```
