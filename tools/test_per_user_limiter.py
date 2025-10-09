#!/usr/bin/env python3
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from per_user_limiter import PerUserLimiter
from config import Config


def main() -> int:
    limiter = PerUserLimiter(limit=Config.PER_USER_HOURLY_LIMIT, window_secs=3600)
    user = "non_whitelist_user"
    wl = next(iter(Config.WHITELIST_HANDLES)) if Config.WHITELIST_HANDLES else "thenighguy"

    allowed = 0
    for i in range(Config.PER_USER_HOURLY_LIMIT):
        if limiter.allow(user):
            allowed += 1
    last = limiter.allow(user)
    print(f"Allowed {allowed} for {user}, 13th allowed? {last}")
    assert allowed == Config.PER_USER_HOURLY_LIMIT and last is False

    # Whitelist should never be blocked
    for i in range(Config.PER_USER_HOURLY_LIMIT + 5):
        assert limiter.allow(wl) is True
    print(f"Whitelist {wl} bypass OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


