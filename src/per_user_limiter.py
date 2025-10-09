import time
from collections import deque, defaultdict
from typing import Deque, Dict
from config import Config


def normalize(username: str) -> str:
    return (username or "").strip().lstrip("@").lower()


class PerUserLimiter:
    def __init__(self, limit: int, window_secs: int = 3600) -> None:
        self.limit = limit
        self.window_secs = window_secs
        self.user_to_timestamps: Dict[str, Deque[float]] = defaultdict(deque)

    def _prune(self, user_key: str, now: float) -> None:
        cutoff = now - self.window_secs
        dq = self.user_to_timestamps[user_key]
        while dq and dq[0] < cutoff:
            dq.popleft()

    def allow(self, username: str) -> bool:
        user_key = normalize(username)
        if user_key in Config.WHITELIST_HANDLES:
            return True

        now = time.time()
        self._prune(user_key, now)
        dq = self.user_to_timestamps[user_key]
        if len(dq) < self.limit:
            dq.append(now)
            return True
        return False

    def count(self, username: str) -> int:
        user_key = normalize(username)
        self._prune(user_key, time.time())
        return len(self.user_to_timestamps[user_key])


