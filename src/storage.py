"""
Simple storage for persisting since_id and processed tweet IDs across runs.
"""
import json
import os
from typing import Optional, Set
from config import Config


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
        """Write since_id to storage file."""
        try:
            data = {"since_id": since_id}
            with open(self.storage_file, "w") as f:
                json.dump(data, f, indent=2)
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
        """Mark a tweet ID as processed (atomic write)."""
        try:
            # Read existing processed IDs
            processed_ids = self.read_processed_ids()
            
            # Add new ID
            processed_ids.add(tweet_id)
            
            # Write back atomically
            data = {"processed_ids": list(processed_ids)}
            with open(self.processed_ids_file, "w") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error marking tweet {tweet_id} as processed: {e}")
    
    def is_processed(self, tweet_id: str) -> bool:
        """Check if a tweet ID has been processed."""
        return tweet_id in self.read_processed_ids()



