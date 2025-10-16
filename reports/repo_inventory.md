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
| Makefile | 0.72 | unknown | Build automation | config | - |
| README.md | 11.09 | md | Project documentation | docs | - |
| REFACTOR_SUMMARY.md | 6.3 | md | Documentation | docs | - |
| RESCUE_PLAN.md | 6.92 | md | Documentation | docs | - |
| RESCUE_RESULT.md | 6.57 | md | Documentation | docs | - |
| TWITTER_V2_MIGRATION.md | 6.77 | md | Documentation | docs | - |
| assets/crybb.jpeg | 38.3 | jpeg | Asset file | asset | - |
| assets/overlays/all_you.png | 581.4 | png | Asset file | asset | - |
| assets/overlays/at_peace.png | 620.68 | png | Asset file | asset | - |
| assets/overlays/be_a_baby.png | 626.78 | png | Asset file | asset | - |
| assets/overlays/big_brain.png | 617.23 | png | Asset file | asset | - |
| assets/overlays/btc.png | 724.73 | png | Asset file | asset | - |
| assets/overlays/cleanup.png | 655.49 | png | Asset file | asset | - |
| assets/overlays/cool_guy.png | 601.13 | png | Asset file | asset | - |
| assets/overlays/cry_about_it.png | 630.4 | png | Asset file | asset | - |
| assets/overlays/cry_patrol.png | 652.04 | png | Asset file | asset | - |
| assets/overlays/dont_cry_bb.png | 563.2 | png | Asset file | asset | - |
| assets/overlays/fired.png | 886.02 | png | Asset file | asset | - |
| assets/overlays/heart.png | 559.68 | png | Asset file | asset | - |
| assets/overlays/hold_my_watch.png | 587.6 | png | Asset file | asset | - |
| assets/overlays/let_him_cook.png | 828.85 | png | Asset file | asset | - |
| assets/overlays/lol.png | 556.1 | png | Asset file | asset | - |
| assets/overlays/love.png | 618.65 | png | Asset file | asset | - |
| assets/overlays/mcdonalds.png | 569.22 | png | Asset file | asset | - |
| assets/overlays/mexican.png | 833.34 | png | Asset file | asset | - |
| assets/overlays/money_bag.png | 644.66 | png | Asset file | asset | - |
| assets/overlays/og.png | 791.88 | png | Asset file | asset | - |
| assets/overlays/poop.png | 576.36 | png | Asset file | asset | - |
| assets/overlays/poors.png | 681.41 | png | Asset file | asset | - |
| assets/overlays/run.png | 578.69 | png | Asset file | asset | - |
| assets/overlays/running.png | 559.91 | png | Asset file | asset | - |
| assets/overlays/scam.png | 548.18 | png | Asset file | asset | - |
| assets/overlays/small_brain.png | 727.04 | png | Asset file | asset | - |
| assets/overlays/star.png | 593.44 | png | Asset file | asset | - |
| assets/overlays/stay_gold.png | 610.15 | png | Asset file | asset | - |
| assets/overlays/stay_poor.png | 738.35 | png | Asset file | asset | - |
| assets/overlays/stupid.png | 736.54 | png | Asset file | asset | - |
| assets/overlays/super_crybb.png | 591.2 | png | Asset file | asset | - |
| assets/overlays/take_my_money.png | 725.59 | png | Asset file | asset | - |
| assets/overlays/tissue.png | 534.35 | png | Asset file | asset | - |
| assets/overlays/ur_a_crybb.png | 590.07 | png | Asset file | asset | - |
| assets/overlays/wtf.png | 929.93 | png | Asset file | asset | - |
| assets/overlays/you_forgot.png | 587.86 | png | Asset file | asset | - |
| debug_mentions.py | 0.6 | py | #!/usr/bin/env python3 | unknown | DEAD |
| docs/ARCHITECTURE.md | 4.75 | md | Documentation | docs | - |
| docs/INDEX.md | 1.13 | md | Documentation | docs | - |
| docs/OPERATIONS.md | 6.16 | md | Documentation | docs | - |
| docs/SPEC.md | 8.34 | md | Documentation | docs | - |
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
| simulation_output/crybb_output_1.jpg | 53.49 | jpg | Image asset | unknown | - |
| simulation_output/crybb_output_2.jpg | 66.53 | jpg | Image asset | unknown | - |
| simulation_output/crybb_output_3.jpg | 61.43 | jpg | Image asset | unknown | - |
| simulation_output/crybb_output_4.jpg | 64.57 | jpg | Image asset | unknown | - |
| simulation_output/simulation_results.json | 3.05 | json | JSON data/config | unknown | - |
| src/__init__.py | 0.09 | py | """ | runtime | - |
| src/ai/nano_banana_client.py | 4.65 | py | AI pipeline module | runtime | DEAD |
| src/ai/prompt_crybb.py | 1.1 | py | AI pipeline module | runtime | - |
| src/auth_v2.py | 6.85 | py | """ | runtime | DEAD |
| src/batch_context.py | 1.76 | py | """ | runtime | DEAD |
| src/config.py | 3.81 | py | Configuration management | runtime | - |
| src/image_processor.py | 1.24 | py | """ | runtime | - |
| src/main.py | 20.13 | py | Main application entry point | runtime | ENTRYPOINT |
| src/per_user_limiter.py | 1.18 | py | Unknown purpose | runtime | DEAD |
| src/pipeline/orchestrator.py | 2.97 | py | Image processing orchestration | runtime | - |
| src/rate_limiter.py | 2.44 | py | """ | runtime | - |
| src/ratelimit.py | 5.26 | py | """ | runtime | DEAD |
| src/retry.py | 2.29 | py | """ | runtime | DEAD |
| src/server.py | 2.48 | py | Health/metrics server | runtime | ENTRYPOINT |
| src/storage.py | 2.72 | py | """ | runtime | DEAD |
| src/twitter_client_dryrun_v2.py | 5.47 | py | Twitter/X API client | runtime | DEAD |
| src/twitter_client_mock_v2.py | 5.6 | py | Twitter/X API client | runtime | DEAD |
| src/twitter_client_v2_new.py | 5.88 | py | Twitter/X API client | runtime | DEAD |
| src/twitter_factory.py | 0.84 | py | Twitter/X API client | runtime | - |
| src/utils.py | 3.27 | py | """ | runtime | - |
| src/x_v2.py | 16.71 | py | """ | runtime | DEAD |
| stress_test_results_1760472875.json | 28.85 | json | JSON data/config | unknown | - |
| stress_test_results_1760472883.json | 28.86 | json | JSON data/config | unknown | - |
| stress_test_results_1760472945.json | 28.87 | json | JSON data/config | unknown | - |
| stress_test_results_1760472974.json | 28.86 | json | JSON data/config | unknown | - |
| test_auth.py | 1.37 | py | #!/usr/bin/env python3 | unknown | ENTRYPOINT |
| test_mentions.py | 0.79 | py | #!/usr/bin/env python3 | unknown | ENTRYPOINT |
| tools/_audit_utils.py | 9.71 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/_diag_lib.py | 3.95 | py | Development tool/diagnostics | dev-tool | - |
| tools/check_queue_state.py | 2.8 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/diagnose_v2.py | 8.98 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/mentions_probe.py | 5.93 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/oauth2_pkce_callback_server.py | 12.82 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/oauth2_store_tokens.py | 1.69 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/probe_x_api.py | 7.23 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/repo_audit.py | 16.16 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/run_ai_smoke.py | 1.12 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/run_diagnostics.py | 15.88 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/run_stress_test.py | 0.75 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/simulate_once.py | 2.29 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/simulate_pfp_pipeline.py | 5.59 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/sleeper_probe.py | 0.71 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/spec_sanity.py | 3.84 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/stress_test_verification.py | 14.03 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_basic_api.py | 7.69 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_basic_plan.py | 7.53 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_batch_snapshot.py | 4.82 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_end_to_end_no_post.py | 4.32 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_media_upload.py | 2.26 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_mention_parsing.py | 7.81 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/test_per_user_limiter.py | 0.93 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |
| tools/verify_auth_paths.py | 7.06 | py | Development tool/diagnostics | dev-tool | ENTRYPOINT |

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
| Remove | src/batch_context.py | Unused module - no imports or entrypoint |
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
git rm src/batch_context.py
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
