#!/usr/bin/env python3
"""
One-shot diagnostics runner for CryBB.

Generates Markdown and JSON reports under reports/.
Never posts to Twitter unless --allow-post=true and mode=live.
"""
import argparse
import io
import json
import os
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

# Ensure repo root on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tools._diag_lib import (
    ok,
    fail,
    skip,
    time_block,
    write_report_md,
    write_report_json,
    ensure_dir,
    timestamp,
    console_table,
    copy_artifact,
)


def git_sha() -> Optional[str]:
    try:
        import subprocess

        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT_DIR).decode().strip()
        return sha
    except Exception:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CryBB diagnostics")
    parser.add_argument("--mode", choices=["auto", "mock", "dryrun", "live"], default="auto")
    parser.add_argument("--allow-post", choices=["false", "true"], default="false")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def step_env_config() -> Dict[str, Any]:
    name = "Environment / Config"
    try:
        os.environ.setdefault("SKIP_CONFIG_VALIDATION", "1")
        from src.config import Config

        required = [
            ("API_KEY", Config.API_KEY),
            ("API_SECRET", Config.API_SECRET),
            ("ACCESS_TOKEN", Config.ACCESS_TOKEN),
            ("ACCESS_SECRET", Config.ACCESS_SECRET),
            ("BEARER_TOKEN", Config.BEARER_TOKEN),
            ("BOT_HANDLE", Config.BOT_HANDLE),
        ]
        missing = [k for k, v in required if not v]
        details = "All required env present" if not missing else f"Missing: {', '.join(missing)}"
        evidence = {
            "TWITTER_MODE": Config.TWITTER_MODE,
            "POLL_SECONDS": Config.POLL_SECONDS,
            "HTTP_TIMEOUT_SECS": Config.HTTP_TIMEOUT_SECS,
        }
        return ok(name, details, evidence) if not missing else fail(name, details, evidence)
    except Exception as e:
        return fail(name, str(e))


def step_dependencies() -> Dict[str, Any]:
    name = "Dependencies"
    evidence: Dict[str, Any] = {}
    required = [
        ("Pillow", "PIL", None),
        ("tweepy", "tweepy", None),
        ("tenacity", "tenacity", None),
    ]
    missing_required: List[str] = []

    for label, module_name, _ in required:
        try:
            __import__(module_name)
            evidence[label] = "present"
        except Exception:
            evidence[label] = "missing"
            missing_required.append(label)

    if missing_required:
        return fail(name, f"Missing required deps: {', '.join(missing_required)}", evidence)
    return ok(name, "Dependencies status recorded", evidence)


def _pick_test_face() -> Optional[str]:
    candidates = [
        os.path.join(ROOT_DIR, "fixtures", "images", "test_face.jpg"),
        os.path.join(ROOT_DIR, "test_images", "face1.jpg"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def step_image_pipeline(artifacts_dir: str) -> Dict[str, Any]:
    name = "Image Pipeline"
    try:
        test_face = _pick_test_face()
        if not test_face:
            return skip(name, "No test face found under fixtures/images/test_face.jpg or test_images/face1.jpg")

        with open(test_face, "rb") as f:
            pfp = f.read()

        from src.image_processor import ImageProcessor
        from src.config import Config

        ip = ImageProcessor()
        out_bytes = ip.render(pfp, watermark=Config.WATERMARK_TEXT)
        if not out_bytes:
            return fail(name, "Renderer returned empty bytes")

        # Save artifacts
        ensure_dir(artifacts_dir)
        inp = os.path.join(artifacts_dir, "pipeline_input.jpg")
        outp = os.path.join(artifacts_dir, "pipeline_output.jpg")
        with open(inp, "wb") as f:
            f.write(pfp)
        with open(outp, "wb") as f:
            f.write(out_bytes)

        return ok(name, f"Rendered {len(out_bytes)} bytes", {"input": inp, "output": outp})
    except Exception as e:
        return fail(name, f"{e}")


def step_author_fallback() -> Dict[str, Any]:
    name = "Author Fallback"
    try:
        # Run simulate_once in mock mode regardless; it respects TWITTER_MODE
        import subprocess
        env = os.environ.copy()
        env["TWITTER_MODE"] = "mock"
        env.setdefault("SKIP_CONFIG_VALIDATION", "1")
        p = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "tools", "simulate_once.py")], env=env, cwd=ROOT_DIR, capture_output=True, text=True)
        if p.returncode != 0:
            return fail(name, f"simulate_once non-zero exit: {p.returncode}\n{p.stderr}")

        # Expect outbox artifact
        outbox_dir = os.path.join(ROOT_DIR, "outbox")
        newest = None
        if os.path.isdir(outbox_dir):
            for d in sorted(os.listdir(outbox_dir), reverse=True):
                dd = os.path.join(outbox_dir, d)
                if os.path.isdir(dd):
                    newest = dd
                    break
        if not newest:
            return fail(name, "No outbox produced by simulate_once")
        required = [os.path.join(newest, "media.jpg"), os.path.join(newest, "reply.json")]
        missing = [p for p in required if not os.path.exists(p)]
        if missing:
            return fail(name, f"Missing outbox files: {', '.join(os.path.basename(m) for m in missing)}")
        return ok(name, "Outbox reply found", {"outbox": newest})
    except Exception as e:
        return fail(name, str(e))


def step_rate_limiter() -> Dict[str, Any]:
    name = "Rate Limiter"
    try:
        from src.rate_limiter import RateLimiter
        rl = RateLimiter()
        author = "tester"
        results = [rl.allow(author) for _ in range(6)]
        if results[:5] == [True, True, True, True, True] and results[5] is False:
            return ok(name, "Denied on 6th request as expected")
        return fail(name, f"Unexpected allow sequence: {results}")
    except Exception as e:
        return fail(name, str(e))


def step_since_id_persistence() -> Dict[str, Any]:
    name = "Since_ID Persistence"
    try:
        from importlib import import_module, reload
        mod = import_module("src.storage")
        Storage = getattr(mod, "Storage")
        s1 = Storage()
        fake_id = 987654321
        s1.write_since_id(fake_id)
        # Re-import module to simulate process boundary
        mod2 = reload(mod)
        Storage2 = getattr(mod2, "Storage")
        s2 = Storage2()
        got = s2.read_since_id()
        if got == fake_id:
            return ok(name, "since_id persisted")
        return fail(name, f"Expected {fake_id}, got {got}")
    except Exception as e:
        return fail(name, str(e))


def step_twitter_probe(mode: str, allow_post: bool) -> Dict[str, Any]:
    name = "Twitter Probe"
    try:
        # If mock mode, skip network probes
        if mode == "mock":
            return skip(name, "Mock mode: no network calls")
        # Try to run the existing probe script
        import subprocess
        env = os.environ.copy()
        env.setdefault("SKIP_CONFIG_VALIDATION", "1")
        p = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "tools", "probe_x_api.py")], env=env, cwd=ROOT_DIR, capture_output=True, text=True)
        details = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
        if p.returncode == 0:
            return ok(name, "Probe passed", {"output": details.strip()[:4000]})
        else:
            return fail(name, "Probe failed", {"output": details.strip()[:4000]})
    except FileNotFoundError:
        return skip(name, "probe_x_api.py not found")
    except Exception as e:
        return fail(name, str(e))


def step_outbox_no_post(mode: str, artifacts_dir: str) -> Dict[str, Any]:
    name = "Outbox / No-Post Result"
    try:
        if mode not in ("mock", "dryrun"):
            return skip(name, "Only applicable to mock/dryrun modes")
        import subprocess
        env = os.environ.copy()
        env["TWITTER_MODE"] = mode
        env.setdefault("SKIP_CONFIG_VALIDATION", "1")
        p = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "tools", "simulate_once.py")], env=env, cwd=ROOT_DIR, capture_output=True, text=True)
        if p.returncode != 0:
            return fail(name, f"simulate_once non-zero exit: {p.returncode}\n{p.stderr}")
        outbox_dir = os.path.join(ROOT_DIR, "outbox")
        newest = None
        if os.path.isdir(outbox_dir):
            for d in sorted(os.listdir(outbox_dir), reverse=True):
                dd = os.path.join(outbox_dir, d)
                if os.path.isdir(dd):
                    newest = dd
                    break
        if not newest:
            return fail(name, "No outbox produced")
        media = os.path.join(newest, "media.jpg")
        reply = os.path.join(newest, "reply.json")
        if not (os.path.exists(media) and os.path.exists(reply)):
            return fail(name, "Missing media.jpg or reply.json")
        # Copy artifacts
        dst_media = copy_artifact(media, artifacts_dir)
        dst_reply = copy_artifact(reply, artifacts_dir)
        return ok(name, "Outbox verified", {"media": dst_media, "reply": dst_reply})
    except Exception as e:
        return fail(name, str(e))


def step_health_server() -> Dict[str, Any]:
    name = "Health Server"
    try:
        import requests
        port = os.getenv("PORT", "8000")
        base = f"http://127.0.0.1:{port}"
        health = f"{base}/health"
        metrics = f"{base}/metrics"
        try:
            r1 = requests.get(health, timeout=2)
            r2 = requests.get(metrics, timeout=2)
            if r1.status_code == 200 and r2.status_code == 200:
                return ok(name, "Health endpoints reachable", {"health": health, "metrics": metrics})
            return fail(name, f"HTTP statuses: /health={r1.status_code} /metrics={r2.status_code}")
        except Exception:
            return skip(name, f"Server not running on {base}")
    except Exception as e:
        return fail(name, str(e))


def step_docker_healthcheck() -> Dict[str, Any]:
    name = "Dockerfile / Healthcheck"
    try:
        dockerfile = os.path.join(ROOT_DIR, "Dockerfile")
        if not os.path.exists(dockerfile):
            return fail(name, "Dockerfile missing")
        with open(dockerfile, "r") as f:
            content = f.read()
        if "HEALTHCHECK" in content.upper():
            return ok(name, "HEALTHCHECK present in Dockerfile")
        # Optional: check docker-compose.yml if present
        compose = os.path.join(ROOT_DIR, "docker-compose.yml")
        if os.path.exists(compose):
            with open(compose, "r") as f:
                if "healthcheck" in f.read():
                    return ok(name, "healthcheck present in docker-compose.yml")
        return skip(name, "No HEALTHCHECK found; consider adding one")
    except Exception as e:
        return fail(name, str(e))


def main() -> int:
    load_dotenv()
    args = parse_args()

    # Resolve mode
    mode = args.mode
    if mode == "auto":
        # Avoid triggering Config.validate at import-time
        os.environ.setdefault("SKIP_CONFIG_VALIDATION", "1")
        from src.config import Config
        mode = Config.TWITTER_MODE
    mode = (mode or "live").lower()
    allow_post = args["allow_post"] if isinstance(args, dict) and "allow_post" in args else (args.allow_post == "true")
    allow_post = True if args.allow_post == "true" else False

    reports_dir = os.path.join(ROOT_DIR, "reports")
    artifacts_dir = os.path.join(reports_dir, "artifacts")
    ensure_dir(reports_dir)
    ensure_dir(artifacts_dir)

    stamp = timestamp()
    md_path = os.path.join(reports_dir, f"diagnostics_{stamp}.md")
    json_path = os.path.join(reports_dir, f"diagnostics_{stamp}.json")

    results: List[Dict[str, Any]] = []

    with time_block("Environment / Config"):
        results.append(step_env_config())
    with time_block("Dependencies"):
        results.append(step_dependencies())
    with time_block("Image Pipeline"):
        results.append(step_image_pipeline(artifacts_dir))
    with time_block("AI Pipeline (nano-banana)"):
        try:
            from src.config import Config
            from src.pipeline.orchestrator import Orchestrator
            orch = Orchestrator(Config)
            # Use fixture or a known public avatar if available
            sample = os.getenv("AI_SMOKE_PFP_URL") or "https://pbs.twimg.com/profile_images/1354481591171891202/Pl0n4YkU.jpg"
            out = orch.render(pfp_url=sample, mention_text="diagnostics")
            ai_path = os.path.join(artifacts_dir, "ai_sample.jpg")
            with open(ai_path, "wb") as f:
                f.write(out)
            results.append(ok("AI Pipeline (nano-banana)", f"bytes={len(out)}", {"output": ai_path}))
        except Exception as e:
            results.append(fail("AI Pipeline (nano-banana)", str(e)))
    with time_block("Author Fallback"):
        results.append(step_author_fallback())
    with time_block("Rate Limiter"):
        results.append(step_rate_limiter())
    with time_block("Since_ID Persistence"):
        results.append(step_since_id_persistence())
    with time_block("Twitter Probe"):
        results.append(step_twitter_probe(mode, allow_post))
    with time_block("Outbox / No-Post Result"):
        results.append(step_outbox_no_post(mode, artifacts_dir))
    with time_block("Health Server"):
        results.append(step_health_server())
    with time_block("Dockerfile / Healthcheck"):
        results.append(step_docker_healthcheck())

    data: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "git_sha": git_sha(),
        "results": results,
        "artifacts": [],
    }

    # Collect artifact references from steps
    for r in results:
        ev = r.get("evidence") or {}
        for key in ("input", "output", "media", "reply"):
            if key in ev and isinstance(ev[key], str) and os.path.exists(ev[key]):
                data["artifacts"].append({"label": key, "path": os.path.relpath(ev[key], ROOT_DIR)})

    # Write reports
    write_report_json(data, json_path)
    write_report_md(data, md_path)

    # Console summary
    print("\n" + console_table(results))
    # Exit code: non-zero if any FAIL
    any_fail = any(r.get("status") == "FAIL" for r in results)
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())


