"""
Simple storage for persisting since_id across runs.
"""
import json
import os
from typing import Optional
from config import Config


class Storage:
    """Simple file-based storage for since_id persistence."""
    
    def __init__(self):
        """Initialize storage."""
        self.storage_file = os.path.join(Config.OUTBOX_DIR, "since_id.json")
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



