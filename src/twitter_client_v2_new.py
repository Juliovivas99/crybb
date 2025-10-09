"""
Modern Twitter API v2 client with OAuth 2.0 authentication.
Replaces the legacy hybrid approach with pure v2 implementation.
"""
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from config import Config
from auth_v2 import create_bearer_session, create_user_session
from x_v2 import XAPIv2Client
from ratelimit import RateLimiter


@dataclass
class UserInfo:
    """Cached user information."""
    id: str
    username: str
    name: str
    profile_image_url: Optional[str] = None


class TwitterClientV2New:
    """
    Modern Twitter API v2 client with OAuth 2.0 authentication.
    
    Key improvements:
    - Pure v2 API implementation with OAuth 2.0 Bearer Token for reads
    - OAuth 2.0 user context for writes (tweets and media upload)
    - Intelligent caching to minimize API calls
    - Centralized rate limiting with adaptive backoff
    - Comprehensive error handling
    """
    
    def __init__(self):
        """Initialize the v2 client with OAuth 2.0 authentication."""
        # Create authentication sessions
        self.bearer_session = create_bearer_session()
        self.user_session = create_user_session()
        
        # Create v2 API client
        self.client = XAPIv2Client(self.bearer_session, self.user_session)
        
        # Centralized rate limiter
        self.rate_limiter = RateLimiter()
        
        print("Twitter API v2 client initialized with OAuth 2.0 authentication")
    
    def get_bot_identity(self) -> Tuple[str, str]:
        """
        Get bot identity with intelligent caching.
        Only calls API once at startup, then uses cached result.
        """
        return self.client.get_me()
    
    def get_mentions(self, since_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get mentions with comprehensive user data expansion to minimize additional API calls.
        Uses expansions to include author and mentioned user data in the response.
        """
        try:
            bot_id, _ = self.get_bot_identity()
            
            # Check if we should back off
            if self.rate_limiter.should_backoff('users/mentions'):
                print("Backing off from mentions due to rate limits")
                return []
            
            mentions = self.client.get_mentions(bot_id, since_id)
            
            # Apply adaptive backoff after mentions fetch
            self.rate_limiter.maybe_sleep('users/mentions')
            
            return mentions
            
        except Exception as e:
            print(f"Error getting mentions: {e}")
            return []
    
    def get_user_by_id(self, user_id: str) -> Optional[UserInfo]:
        """
        Get user by ID with intelligent caching.
        Checks cache first, only makes API call if needed.
        """
        # Check cache first
        for cached_user in self.client._user_cache.values():
            if cached_user.id == user_id:
                return cached_user
        
        try:
            # Check if we should back off
            if self.rate_limiter.should_backoff('users'):
                print(f"Backing off from user lookup for {user_id}")
                return None
            
            # Use v2 API to get user by ID
            url = f"https://api.twitter.com/2/users/{user_id}"
            params = {
                'user.fields': 'id,username,name,profile_image_url'
            }
            
            response = self.bearer_session.get(url, params=params)
            self.rate_limiter.update_rate_limits('users', 
                int(response.headers.get('x-rate-limit-limit', 0)),
                int(response.headers.get('x-rate-limit-remaining', 0)),
                int(response.headers.get('x-rate-limit-reset', 0))
            )
            
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data:
                user_data = data['data']
                user_info = UserInfo(
                    id=user_data['id'],
                    username=user_data['username'],
                    name=user_data['name'],
                    profile_image_url=user_data.get('profile_image_url')
                )
                
                # Cache the result
                self.client._user_cache[user_info.id] = user_info
                return user_info
            
        except Exception as e:
            print(f"Error getting user by ID {user_id}: {e}")
        
        return None
    
    def get_user_by_username(self, username: str) -> Optional[UserInfo]:
        """
        Get user by username with intelligent caching.
        Checks cache first, only makes API call if needed.
        """
        return self.client.get_user_by_username(username)
    
    def download_bytes(self, url: str) -> Optional[bytes]:
        """Download image bytes from URL with proper error handling."""
        try:
            response = self.bearer_session.session.get(url, timeout=Config.HTTP_TIMEOUT_SECS)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
            return None
    
    def upload_media(self, image_bytes: bytes, filename: str = "crybb.jpg") -> Optional[str]:
        """
        Upload media using Twitter's v1.1 media upload endpoint with OAuth1a.
        """
        try:
            return self.client.media_upload(image_bytes)
        except Exception as e:
            print(f"Error uploading media: {e}")
            return None
    
    def create_tweet(self, text: str, in_reply_to_tweet_id: Optional[str] = None, 
                    media_ids: Optional[List[str]] = None) -> Optional[str]:
        """
        Create a tweet using Twitter API v2.
        Supports text, replies, and media attachments.
        """
        return self.client.create_reply(text, in_reply_to_tweet_id, media_ids)
    
    def reply_with_image(self, in_reply_to_tweet_id: str, text: str, image_bytes: bytes) -> None:
        """
        Reply to a tweet with an image using pure v2 API.
        This is the main method used by the bot for replying.
        """
        self.client.reply_with_image(in_reply_to_tweet_id, text, image_bytes)
    
    def get_rate_limit_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current rate limit status for monitoring."""
        return self.client.get_rate_limit_status()
    
    def clear_cache(self) -> None:
        """Clear all caches (useful for testing or memory management)."""
        self.client._user_cache.clear()
        self.client._bot_identity = None
        self.client._bot_identity_fetched_at = None
        print("All caches cleared")
