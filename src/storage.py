"""
Simple storage for persisting since_id and processed tweet IDs across runs.
"""
import json
import os
from typing import Optional, Set
from src.config import Config


class Storage:
    """Simple file-based storage for since_id and processed tweet ID persistence."""
    
    def __init__(self):
        """Initialize storage."""
        self.storage_file = os.path.join(Config.OUTBOX_DIR, "since_id.json")
        self.processed_ids_file = os.path.join(Config.OUTBOX_DIR, "processed_ids.json")
        os.makedirs(Config.OUTBOX_DIR, exist_ok=True)
    
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



