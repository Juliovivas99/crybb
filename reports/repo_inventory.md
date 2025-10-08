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
| .env | 0.92 | unknown | Unknown purpose | unknown | - |
| .env.example.min | 0.36 | min | Unknown purpose | unknown | - |
| CHANGES_SUMMARY.md | 3.93 | md | Documentation | docs | - |
| DEPLOYMENT_GUIDE.md | 7.83 | md | Documentation | docs | - |
| DIFF_SUMMARY.md | 6.56 | md | Documentation | docs | - |
| DIGITALOCEAN_DEPLOYMENT.md | 4.94 | md | Documentation | docs | - |
| LIVE_TESTING_SETUP.md | 4.29 | md | Documentation | docs | - |
| Makefile | 0.61 | unknown | Build automation | config | - |
| README.md | 10.99 | md | Project documentation | docs | - |
| assets/crybb.jpeg | 0.03 | jpeg | Asset file | asset | - |
| env.example | 0.56 | example | Unknown purpose | unknown | - |
| fixtures/mentions.json | 0.13 | json | Test fixture | asset | - |
| fixtures/users.json | 0.29 | json | Test fixture | asset | - |
| requirements.txt | 0.13 | txt | Python dependencies | config | - |
| scripts/crybb-bot.service | 0.99 | service | Unknown purpose | unknown | - |
| scripts/deploy.sh | 2.75 | sh | #!/usr/bin/env bash | unknown | - |
| scripts/deploy_complete.sh | 10.21 | sh | #!/usr/bin/env bash | unknown | - |
| scripts/deployment_summary.sh | 2.29 | sh | #!/usr/bin/env bash | unknown | - |
| scripts/harden.sh | 2.0 | sh | #!/usr/bin/env bash | unknown | - |
| scripts/harden_complete.sh | 6.83 | sh | #!/usr/bin/env bash | unknown | - |
| scripts/test_health.sh | 0.48 | sh | #!/usr/bin/env bash | unknown | - |
| scripts/update.sh | 0.72 | sh | #!/usr/bin/env bash | unknown | - |
| src/__init__.py | 0.09 | py | """ | runtime | - |
| src/ai/nano_banana_client.py | 4.8 | py | AI pipeline module | runtime | - |
| src/ai/prompt_crybb.py | 0.45 | py | AI pipeline module | runtime | - |
| src/config.py | 3.96 | py | Configuration management | runtime | - |
| src/image_processor.py | 1.24 | py | """ | runtime | - |
| src/main.py | 7.91 | py | Main application entry point | runtime | ENTRYPOINT |
| src/pipeline/orchestrator.py | 2.54 | py | Image processing orchestration | runtime | - |
| src/rate_limiter.py | 2.08 | py | """ | runtime | - |
| src/retry.py | 2.45 | py | """ | runtime | - |
| src/server.py | 1.39 | py | Health/metrics server | runtime | ENTRYPOINT |
| src/storage.py | 1.13 | py | """ | runtime | DEAD |
| src/twitter_client_dryrun.py | 3.85 | py | Twitter/X API client | runtime | DEAD |
| src/twitter_client_live.py | 6.01 | py | Twitter/X API client | runtime | DEAD |
| src/twitter_client_mock.py | 3.86 | py | Twitter/X API client | runtime | DEAD |
| src/twitter_factory.py | 0.49 | py | Twitter/X API client | runtime | - |
| src/utils.py | 2.74 | py | """ | runtime | - |
| tools/_audit_utils.py | 9.71 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/_diag_lib.py | 3.94 | py | Development tool/diagnostics | dev-tool | - |
| tools/probe_x_api.py | 7.23 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/repo_audit.py | 16.16 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/run_ai_smoke.py | 1.82 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/run_diagnostics.py | 14.51 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/simulate_once.py | 2.29 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_basic_api.py | 7.68 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_basic_plan.py | 7.53 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |

## Dependencies Analysis

### Unused Dependencies

- Pillow
- python-dotenv

## Environment Variables

### Used Variables
- ACCESS_SECRET
- ACCESS_TOKEN
- AI_MAX_ATTEMPTS
- AI_MAX_CONCURRENCY
- API_KEY
- API_SECRET
- BEARER_TOKEN
- BOT_HANDLE
- CLIENT_ID
- CLIENT_SECRET
- CRYBB_STYLE_URL
- FIXTURES_DIR
- HTTP_TIMEOUT_SECS
- IMAGE_PIPELINE
- OUTBOX_DIR
- POLL_SECONDS
- PORT
- REPLICATE_API_TOKEN
- REPLICATE_MODEL
- REPLICATE_POLL_INTERVAL_SECS
- REPLICATE_TIMEOUT_SECS
- SKIP_CONFIG_VALIDATION
- TWITTER_MODE

## Lean-Down Proposal

| Action | Path | Reason |
|--------|------|--------|
| Remove | src/twitter_client_live.py | Unused module - no imports or entrypoint |
| Remove | src/twitter_client_mock.py | Unused module - no imports or entrypoint |
| Remove | src/storage.py | Unused module - no imports or entrypoint |
| Remove | src/twitter_client_dryrun.py | Unused module - no imports or entrypoint |

## Next Actions

### Commands to Execute

```bash
git rm src/twitter_client_live.py
```

```bash
git rm src/twitter_client_mock.py
```

```bash
git rm src/storage.py
```

```bash
git rm src/twitter_client_dryrun.py
```
