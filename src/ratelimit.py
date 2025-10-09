"""
Centralized rate limiting and adaptive polling for X API v2.
Provides intelligent backoff and caching strategies.
"""
import time
from typing import Dict, Optional
from dataclasses import dataclass
from config import Config


@dataclass
class RateLimitInfo:
    """Rate limit information."""
    limit: int
    remaining: int
    reset: int
    retry_after: Optional[int] = None


class RateLimiter:
    """Centralized rate limiter with adaptive polling."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self._rate_limits: Dict[str, RateLimitInfo] = {}
        self._last_request_time = 0.0
        self._min_interval = 0.1  # 100ms minimum between requests
        
        # Adaptive polling
        self._base_poll_seconds = Config.POLL_SECONDS
        self._current_poll_seconds = self._base_poll_seconds
        self._max_poll_seconds = 300  # 5 minutes max
        self._backoff_multiplier = 4
    
    def update_rate_limits(self, endpoint: str, limit: int, remaining: int, reset: int) -> None:
        """Update rate limit information for an endpoint."""
        self._rate_limits[endpoint] = RateLimitInfo(
            limit=limit,
            remaining=remaining,
            reset=reset
        )
    
    def should_backoff(self, endpoint: str) -> bool:
        """Check if we should back off for an endpoint."""
        if endpoint not in self._rate_limits:
            return False
        
        rate_info = self._rate_limits[endpoint]
        current_time = time.time()
        
        # Back off if remaining < 2 or if we're close to reset with few requests
        if rate_info.remaining < 2:
            return True
        
        time_until_reset = rate_info.reset - current_time
        if time_until_reset < 60 and rate_info.remaining <= 5:
            return True
        
        return False
    
    def maybe_sleep(self, endpoint: str) -> None:
        """Sleep if rate limit is low."""
        if endpoint not in self._rate_limits:
            return
        
        rate_info = self._rate_limits[endpoint]
        current_time = time.time()
        
        # Sleep until reset + 5 seconds if remaining < 2
        if rate_info.remaining < 2:
            time_until_reset = rate_info.reset - current_time
            if time_until_reset > 0:
                sleep_time = time_until_reset + 5
                print(f"⚠️  Rate limit low ({rate_info.remaining}/{rate_info.limit}), sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
    
    def enforce_min_interval(self) -> None:
        """Enforce minimum time between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_interval:
            sleep_time = self._min_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def calculate_adaptive_poll_interval(self) -> int:
        """Calculate adaptive polling interval based on rate limits."""
        # Check mentions rate limit
        mentions_status = self._rate_limits.get('users/mentions')
        if mentions_status:
            remaining = mentions_status.remaining
            limit = mentions_status.limit
            
            # If we're running low on requests, increase wait time
            if remaining < 5:
                self._current_poll_seconds = min(
                    self._base_poll_seconds * self._backoff_multiplier,
                    self._max_poll_seconds
                )
            elif remaining < 15:
                self._current_poll_seconds = min(
                    self._base_poll_seconds * 2,
                    self._max_poll_seconds
                )
            elif remaining < 30:
                self._current_poll_seconds = int(self._base_poll_seconds * 1.5)
            else:
                # Gradually reduce back to base
                if self._current_poll_seconds > self._base_poll_seconds:
                    self._current_poll_seconds = max(
                        int(self._current_poll_seconds * 0.9),
                        self._base_poll_seconds
                    )
        
        # Check other endpoints
        for endpoint, rate_info in self._rate_limits.items():
            if endpoint != 'users/mentions' and rate_info.remaining < 5:
                # Conservative wait if any endpoint is low
                self._current_poll_seconds = min(
                    self._base_poll_seconds * 2,
                    self._max_poll_seconds
                )
                break
        
        return self._current_poll_seconds
    
    def get_rate_limit_status(self) -> Dict[str, Dict[str, any]]:
        """Get current rate limit status for all endpoints."""
        status = {}
        for endpoint, rate_info in self._rate_limits.items():
            status[endpoint] = {
                'limit': rate_info.limit,
                'remaining': rate_info.remaining,
                'reset': rate_info.reset,
                'reset_time': time.ctime(rate_info.reset),
                'should_backoff': self.should_backoff(endpoint)
            }
        return status
    
    def reset_poll_interval(self) -> None:
        """Reset polling interval to base value."""
        self._current_poll_seconds = self._base_poll_seconds

