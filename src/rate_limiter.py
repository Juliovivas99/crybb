"""
Rate limiting module for CryBB Maker Bot.
Implements in-memory per-user rate limiting.
"""
from collections import deque
from typing import Dict
import time
from config import Config

class RateLimiter:
    """In-memory rate limiter using sliding window."""
    
    def __init__(self):
        """Initialize rate limiter."""
        # Dictionary mapping user_id to deque of timestamps
        self.user_requests: Dict[str, deque] = {}
        self.window_size = 3600  # 1 hour in seconds
        self.max_requests = Config.RATE_LIMIT_PER_HOUR
    
    def allow(self, author_id: str) -> bool:
        """Check if user is allowed to make a request."""
        current_time = time.time()
        
        # Get or create user's request history
        if author_id not in self.user_requests:
            self.user_requests[author_id] = deque()
        
        user_deque = self.user_requests[author_id]
        
        # Remove old requests outside the window
        while user_deque and user_deque[0] <= current_time - self.window_size:
            user_deque.popleft()
        
        # Check if under limit
        if len(user_deque) < self.max_requests:
            user_deque.append(current_time)
            return True
        
        return False
    
    def get_remaining_requests(self, author_id: str) -> int:
        """Get remaining requests for a user."""
        current_time = time.time()
        
        if author_id not in self.user_requests:
            return self.max_requests
        
        user_deque = self.user_requests[author_id]
        
        # Remove old requests
        while user_deque and user_deque[0] <= current_time - self.window_size:
            user_deque.popleft()
        
        return max(0, self.max_requests - len(user_deque))
    
    def get_reset_time(self, author_id: str) -> float:
        """Get time when user's rate limit resets."""
        if author_id not in self.user_requests or not self.user_requests[author_id]:
            return time.time()
        
        oldest_request = self.user_requests[author_id][0]
        return oldest_request + self.window_size
    
    def calculate_adaptive_poll_interval(self) -> int:
        """Calculate adaptive polling interval based on rate limits."""
        # Simple implementation - return base poll interval
        # This method is called by the main loop but the actual rate limiting
        # is handled by the Twitter client's rate limiting
        return Config.POLL_SECONDS