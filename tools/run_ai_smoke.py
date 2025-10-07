#!/usr/bin/env python3
import argparse
import os
import sys
from dotenv import load_dotenv


# Ensure repo root on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="AI smoke test (nano-banana)")
    parser.add_argument("--pfp-url", required=True)
    args = parser.parse_args()

    try:
        from src.config import Config
        from src.pipeline.orchestrator import Orchestrator
        orch = Orchestrator(Config)
        out = orch.render(pfp_url=args.pfp_url, mention_text="ai_smoke")
        artifacts_dir = os.path.join(ROOT_DIR, "reports", "artifacts")
        os.makedirs(artifacts_dir, exist_ok=True)
        out_path = os.path.join(artifacts_dir, "ai_smoke.jpg")
        with open(out_path, "wb") as f:
            f.write(out)
        print(f"PASS - wrote {len(out)} bytes to {out_path}")
        return 0
    except Exception as e:
        print(f"FAIL - {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())


