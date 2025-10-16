#!/usr/bin/env python3
import os, sys, re, json, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

FILES_MUST_EXIST = [
    "docs/SPEC.md",
    "docs/ARCHITECTURE.md",
    "docs/OPERATIONS.md",
    "docs/INDEX.md",
    "src/main.py",
    "src/x_v2.py",
    "src/twitter_client_v2_new.py",
    "src/twitter_factory.py",
    "src/storage.py",
    "src/batch_context.py",
    "src/per_user_limiter.py",
    "src/server.py",
]

SYMBOLS = {
    "src/main.py": [
        r"class\s+CryBBBot",
        r"def\s+process_mention\(",
        r"def\s+run_polling_loop\("
    ],
    "src/x_v2.py": [
        r"class\s+XAPIv2Client",
        r"def\s+_capture_rate_limits\(",
        r"def\s+get_mentions\(",
        r"def\s+media_upload\(",
        r"def\s+create_reply\(",
        r"def\s+reply_with_image\(",
        r"def\s+get_user_tweets\(",
        r"def\s+retweet_v11\("
    ],
    "src/twitter_client_v2_new.py": [
        r"class\s+TwitterClientV2New",
        r"def\s+get_mentions\(",
        r"def\s+reply_with_image\(",
        r"def\s+create_reply_text\("
    ],
    "src/storage.py": [
        r"class\s+Storage",
        r"def\s+read_since_id\(",
        r"def\s+write_since_id\(",
        r"def\s+read_processed_ids\(",
        r"def\s+mark_processed\(",
        r"def\s+is_processed\("
    ],
    "src/batch_context.py": [
        r"class\s+ProcessingContext",
        r"def\s+get_user\(",
        r"def\s+pin_user\("
    ],
    "src/per_user_limiter.py": [
        r"class\s+PerUserLimiter",
        r"def\s+allow\(",
        r"def\s+count\("
    ],
    "src/server.py": [
        r"app\s*=\s*FastAPI",
        r"@app\.get\(\"/health\"\)",
        r"@app\.get\(\"/metrics\"\)",
        r"def\s+update_metrics\("
    ]
}

def grep_file(path, patterns):
    ok = True
    found = {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for pat in patterns:
        m = re.search(pat, content, re.MULTILINE)
        found[pat] = bool(m)
        if not m:
            ok = False
    return ok, found

def import_exists(module_path):
    spec = importlib.util.spec_from_file_location("tmpmod", module_path)
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    os.chdir(ROOT)
    # Ensure imports resolve to our src/ modules and skip config validation side effects
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    os.environ.setdefault("SKIP_CONFIG_VALIDATION", "1")

    # 1) Verify repository facts
    missing = [rel for rel in FILES_MUST_EXIST if not os.path.exists(rel)]
    if missing:
        print(json.dumps({"files_ok": False, "missing": missing}, indent=2))
        sys.exit(1)

    # 2) Grep verified symbols
    grep_results = {}
    all_ok = True
    for rel, pats in SYMBOLS.items():
        ok, found = grep_file(rel, pats)
        grep_results[rel] = found
        if not ok:
            all_ok = False

    # 3) Import key modules (import only)
    imports_ok = True
    import_errs = {}
    for rel in [
        "src/main.py",
        "src/x_v2.py",
        "src/twitter_client_v2_new.py",
        "src/twitter_factory.py",
        "src/storage.py",
        "src/batch_context.py",
        "src/per_user_limiter.py",
        "src/server.py",
    ]:
        ok, err = import_exists(os.path.join(ROOT, rel))
        if not ok:
            imports_ok = False
            import_errs[rel] = err

    summary = {
        "files_ok": True,
        "symbols_ok": all_ok,
        "imports_ok": imports_ok,
        "grep_results": grep_results,
        "import_errors": import_errs,
    }
    print(json.dumps(summary, indent=2))
    if not (summary["files_ok"] and summary["symbols_ok"] and summary["imports_ok"]):
        sys.exit(2)

if __name__ == "__main__":
    main()


