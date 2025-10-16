"""
Batch processing context for mentions handling.
Provides snapshot-based user resolution to avoid cache expiry issues.
"""
from dataclasses import dataclass, field
from typing import Dict, Any
import time


@dataclass
class ProcessingContext:
    """Context for processing a batch of mentions with user data snapshots."""
    
    # Lowercased username -> minimal user snapshot
    batch_users: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Optional inflight pinning for long-running tasks
    inflight_users: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # seconds to keep inflight pins alive
    inflight_ttl_secs: int = 3600

    def get_user(self, username_lc: str) -> Dict[str, Any] | None:
        """Get user data from batch snapshot or inflight pins."""
        now = time.time()
        
        # 1) Check batch snapshot first
        u = self.batch_users.get(username_lc)
        if u:
            return u
            
        # 2) Check inflight pins
        pin = self.inflight_users.get(username_lc)
        if pin and pin.get("expires_at", 0) > now:
            return pin["data"]
            
        return None

    def pin_user(self, username_lc: str, user_min: Dict[str, Any]) -> None:
        """Pin user data for long-running tasks."""
        self.inflight_users[username_lc] = {
            "data": user_min,
            "expires_at": time.time() + self.inflight_ttl_secs
        }
    
    def prune_expired_pins(self) -> None:
        """Remove expired inflight pins to prevent memory leaks."""
        now = time.time()
        expired_keys = [
            key for key, pin in self.inflight_users.items()
            if pin.get("expires_at", 0) <= now
        ]
        for key in expired_keys:
            del self.inflight_users[key]
