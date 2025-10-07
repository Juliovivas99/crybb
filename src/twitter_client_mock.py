"""
Mock Twitter client for testing and development.
"""
import json
import os
from typing import Dict, List, Optional, Tuple
from .config import Config


class TwitterClientMock:
    """Mock Twitter client that simulates API responses."""
    
    def __init__(self):
        """Initialize mock client."""
        self.bot_id = "123456789"
        self.bot_handle = Config.BOT_HANDLE
    
    def get_bot_identity(self) -> Tuple[str, str]:
        """Return mock bot identity."""
        return self.bot_id, self.bot_handle
    
    def get_mentions(self, since_id: Optional[str] = None) -> List[object]:
        """Return mock mentions."""
        # Return empty list for mock
        return []
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, str]]:
        """Return mock user by ID."""
        return {
            "id": str(user_id),
            "username": "mockuser",
            "name": "Mock User",
            "profile_image_url": "https://pbs.twimg.com/profile_images/1701423369848893440/kp3HKM8o_400x400.jpg"
        }
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, str]]:
        """Return mock user by username."""
        return {
            "id": "987654321",
            "username": username,
            "name": f"Mock {username}",
            "profile_image_url": "https://pbs.twimg.com/profile_images/1701423369848893440/kp3HKM8o_400x400.jpg"
        }
    
    def download_bytes(self, url: str) -> Optional[bytes]:
        """Mock download - return a small test image."""
        # Return a minimal JPEG header
        return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    
    def reply_with_image(self, tweet_id: str, text: str, image_bytes: bytes) -> None:
        """Mock reply - write to outbox directory."""
        outbox_dir = Config.OUTBOX_DIR
        os.makedirs(outbox_dir, exist_ok=True)
        
        # Create timestamp-based directory
        import time
        timestamp = int(time.time())
        reply_dir = os.path.join(outbox_dir, f"{timestamp}_{tweet_id}")
        os.makedirs(reply_dir, exist_ok=True)
        
        # Write reply data
        reply_data = {
            "tweet_id": tweet_id,
            "text": text,
            "timestamp": timestamp
        }
        
        with open(os.path.join(reply_dir, "reply.json"), "w") as f:
            json.dump(reply_data, f, indent=2)
        
        # Write image
        with open(os.path.join(reply_dir, "media.jpg"), "wb") as f:
            f.write(image_bytes)
        
        print(f"Mock reply written to {reply_dir}")
