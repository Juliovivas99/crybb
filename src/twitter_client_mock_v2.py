"""
Mock Twitter client v2 for testing and development.
Provides realistic mock responses for all API endpoints.
"""
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from src.config import Config


@dataclass
class UserInfo:
    """Mock user information."""
    id: str
    username: str
    name: str
    profile_image_url: Optional[str] = None
    verified: Optional[bool] = None


class TwitterClientMockV2:
    """
    Mock Twitter client v2 for testing and development.
    Provides realistic responses without making actual API calls.
    """
    
    def __init__(self):
        """Initialize mock client."""
        self.bot_id = "123456789"
        self.bot_handle = Config.BOT_HANDLE
        
        # Mock user cache
        self._user_cache: Dict[str, UserInfo] = {}
        
        # Mock mentions data
        self._mock_mentions = [
            {
                "id": "1234567890123456789",
                "text": f"@{Config.BOT_HANDLE} @testuser make me crybb",
                "author_id": "987654321",
                "created_at": "2024-01-01T12:00:00.000Z",
                "author": {
                    "id": "987654321",
                    "username": "testuser",
                    "name": "Test User",
                    "profile_image_url": "https://pbs.twimg.com/profile_images/1701423369848893440/kp3HKM8o_400x400.jpg"
                }
            }
        ]
        
        print("Twitter API v2 mock client initialized")
    
    def get_bot_identity(self) -> Tuple[str, str]:
        """Return mock bot identity."""
        return self.bot_id, self.bot_handle
    
    def get_mentions(self, since_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return mock mentions for testing."""
        # Filter by since_id if provided
        if since_id:
            filtered_mentions = [
                mention for mention in self._mock_mentions 
                if int(mention["id"]) > int(since_id)
            ]
            return filtered_mentions
        
        return self._mock_mentions.copy()
    
    def get_user_by_id(self, user_id: str) -> Optional[UserInfo]:
        """Return mock user by ID."""
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        
        user_info = UserInfo(
            id=user_id,
            username="mockuser",
            name="Mock User",
            profile_image_url="https://pbs.twimg.com/profile_images/1701423369848893440/kp3HKM8o_400x400.jpg",
            verified=True
        )
        
        self._user_cache[user_id] = user_info
        return user_info
    
    def get_user_by_username(self, username: str) -> Optional[UserInfo]:
        """Return mock user by username."""
        # Check cache first
        for cached_user in self._user_cache.values():
            if cached_user.username == username:
                return cached_user
        
        user_info = UserInfo(
            id="111222333",
            username=username,
            name=f"Mock {username}",
            profile_image_url="https://pbs.twimg.com/profile_images/1701423369848893440/kp3HKM8o_400x400.jpg",
            verified=True
        )
        
        self._user_cache[user_info.id] = user_info
        return user_info
    
    def download_bytes(self, url: str) -> Optional[bytes]:
        """Mock download - return a small test image."""
        # Return a minimal JPEG header
        return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    
    def upload_media(self, image_bytes: bytes, filename: str = "crybb.jpg") -> Optional[str]:
        """Mock media upload - return fake media ID."""
        print(f"Mock media upload: {len(image_bytes)} bytes")
        return "mock_media_id_12345"
    
    def create_tweet(self, text: str, in_reply_to_tweet_id: Optional[str] = None, 
                    media_ids: Optional[List[str]] = None) -> Optional[str]:
        """Mock tweet creation - return fake tweet ID."""
        print(f"Mock tweet creation: {text}")
        if in_reply_to_tweet_id:
            print(f"Replying to: {in_reply_to_tweet_id}")
        if media_ids:
            print(f"With media: {media_ids}")
        return "mock_tweet_id_67890"
    
    def reply_with_image(self, in_reply_to_tweet_id: str, text: str, image_bytes: bytes) -> None:
        """Mock reply with image."""
        print(f"Mock reply to {in_reply_to_tweet_id}: {text}")
        print(f"Image size: {len(image_bytes)} bytes")
        print("Mock reply completed successfully")
    
    def get_rate_limit_status(self) -> Dict[str, Dict[str, Any]]:
        """Return mock rate limit status."""
        return {
            "/users/me": {"limit": 75, "remaining": 75, "reset": int(time.time()) + 900},
            "/users/mentions": {"limit": 75, "remaining": 75, "reset": int(time.time()) + 900},
            "/users": {"limit": 75, "remaining": 75, "reset": int(time.time()) + 900},
            "/tweets": {"limit": 300, "remaining": 300, "reset": int(time.time()) + 900}
        }
    
    def clear_cache(self) -> None:
        """Clear all caches."""
        self._user_cache.clear()
        print("Mock cache cleared")
