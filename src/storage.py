"""
Simple storage for persisting since_id and processed tweet IDs across runs.
"""
import json
import os
import time
from typing import Optional, Set, Dict, Tuple
from src.config import Config


class Storage:
    """Simple file-based storage for since_id and processed tweet ID persistence."""
    
    def __init__(self):
        """Initialize storage."""
        self.storage_file = os.path.join(Config.OUTBOX_DIR, "since_id.json")
        self.processed_ids_file = os.path.join(Config.OUTBOX_DIR, "processed_ids.json")
        self.conversation_cache_file = os.path.join(Config.OUTBOX_DIR, "conversation_cache.json")
        os.makedirs(Config.OUTBOX_DIR, exist_ok=True)
        
        # In-memory conversation cache with TTL
        self._conversation_cache: Dict[Tuple[str, str], float] = {}
        self._conversation_cache_ttl = 45 * 60  # 45 minutes
        self._load_conversation_cache()
    
    def read_since_id(self) -> Optional[str]:
        """Read since_id from storage file."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, "r") as f:
                    data = json.load(f)
                    return data.get("since_id")
        except Exception as e:
            print(f"Error reading since_id: {e}")
        
        return None
    
    def write_since_id(self, since_id: str) -> None:
        """Atomically write since_id to storage file."""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            data = {"since_id": since_id}
            tmp = f"{self.storage_file}.tmp"
            with open(tmp, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, self.storage_file)  # atomic on POSIX
        except Exception as e:
            print(f"Error writing since_id: {e}")
    
    def read_processed_ids(self) -> Set[str]:
        """Read processed tweet IDs from storage file."""
        try:
            if os.path.exists(self.processed_ids_file):
                with open(self.processed_ids_file, "r") as f:
                    data = json.load(f)
                    return set(data.get("processed_ids", []))
        except Exception as e:
            print(f"Error reading processed_ids: {e}")
        
        return set()
    
    def mark_processed(self, tweet_id: str) -> None:
        """Atomically mark a tweet as processed."""
        try:
            os.makedirs(os.path.dirname(self.processed_ids_file), exist_ok=True)
            current = self.read_processed_ids()
            if tweet_id in current:
                return
            current.add(tweet_id)
            tmp = f"{self.processed_ids_file}.tmp"
            with open(tmp, "w") as f:
                json.dump({"processed_ids": sorted(list(current))}, f, indent=2)
            os.replace(tmp, self.processed_ids_file)  # atomic on POSIX
        except Exception as e:
            print(f"Error marking {tweet_id} processed: {e}")
    
    def is_processed(self, tweet_id: str) -> bool:
        """Check if a tweet ID has been processed."""
        return tweet_id in self.read_processed_ids()
    
    def _load_conversation_cache(self) -> None:
        """Load conversation cache from file."""
        try:
            if os.path.exists(self.conversation_cache_file):
                with open(self.conversation_cache_file, "r") as f:
                    data = json.load(f)
                    # Convert string keys back to tuples
                    for key_str, timestamp in data.items():
                        conversation_id, target_username = key_str.split(":", 1)
                        self._conversation_cache[(conversation_id, target_username)] = timestamp
        except Exception as e:
            print(f"Error loading conversation cache: {e}")
    
    def _save_conversation_cache(self) -> None:
        """Save conversation cache to file."""
        try:
            # Convert tuple keys to strings for JSON serialization
            data = {f"{conv_id}:{target}": timestamp 
                   for (conv_id, target), timestamp in self._conversation_cache.items()}
            
            tmp = f"{self.conversation_cache_file}.tmp"
            with open(tmp, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, self.conversation_cache_file)  # atomic on POSIX
        except Exception as e:
            print(f"Error saving conversation cache: {e}")
    
    def _prune_conversation_cache(self) -> None:
        """Remove expired entries from conversation cache."""
        now = time.time()
        expired_keys = [
            key for key, timestamp in self._conversation_cache.items()
            if now - timestamp > self._conversation_cache_ttl
        ]
        for key in expired_keys:
            del self._conversation_cache[key]
    
    def check_conversation_dedupe(self, conversation_id: str, target_username: str) -> bool:
        """
        Check if we've already processed this conversation-target pair recently.
        
        Args:
            conversation_id: The conversation ID
            target_username: The target username (normalized)
            
        Returns:
            True if we should skip (already processed), False if we should proceed
        """
        self._prune_conversation_cache()
        
        key = (conversation_id, target_username.lower())
        now = time.time()
        
        if key in self._conversation_cache:
            timestamp = self._conversation_cache[key]
            if now - timestamp < self._conversation_cache_ttl:
                return True  # Skip - already processed recently
        
        return False  # Proceed
    
    def record_conversation_dedupe(self, conversation_id: str, target_username: str) -> None:
        """
        Record that we've processed this conversation-target pair.
        
        Args:
            conversation_id: The conversation ID
            target_username: The target username (normalized)
        """
        key = (conversation_id, target_username.lower())
        self._conversation_cache[key] = time.time()
        self._save_conversation_cache()



