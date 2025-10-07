"""
Live Twitter client using Tweepy API.
"""
import json
import os
import time
import requests
import tweepy
from typing import Dict, List, Optional, Tuple
from .config import Config


class TwitterClientLive:
    """Live Twitter client using Tweepy API."""
    
    def __init__(self):
        """Initialize live client with Tweepy."""
        self.bot_id = "123456789"
        self.bot_handle = Config.BOT_HANDLE
        
        # Initialize Tweepy clients
        v1_auth = tweepy.OAuth1UserHandler(
            Config.API_KEY, Config.API_SECRET,
            Config.ACCESS_TOKEN, Config.ACCESS_SECRET
        )
        self.v1_client = tweepy.API(v1_auth, wait_on_rate_limit=True)
        
        self.v2_client = tweepy.Client(
            bearer_token=Config.BEARER_TOKEN,
            consumer_key=Config.API_KEY,
            consumer_secret=Config.API_SECRET,
            access_token=Config.ACCESS_TOKEN,
            access_token_secret=Config.ACCESS_SECRET,
            wait_on_rate_limit=True,
        )
    
    def get_bot_identity(self) -> Tuple[str, str]:
        """Get bot identity from API."""
        try:
            me = self.v2_client.get_me()
            if me and me.data:
                return str(me.data.id), me.data.username
        except Exception as e:
            print(f"Error getting bot identity: {e}")
        
        return self.bot_id, self.bot_handle
    
    def get_mentions(self, since_id: Optional[str] = None) -> List[object]:
        """Get mentions from Twitter API."""
        try:
            me = self.v2_client.get_me()
            if not me or not me.data:
                return []
            
            params = {
                "max_results": 10,
                "tweet.fields": "created_at,author_id"
            }
            if since_id:
                params["since_id"] = since_id
            
            response = self.v2_client.get_users_mentions(
                me.data.id,
                **params
            )
            
            return response.data if response and response.data else []
        except Exception as e:
            print(f"Error getting mentions: {e}")
            return []
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, str]]:
        """Get user by ID from Twitter API."""
        try:
            response = self.v2_client.get_user(
                id=user_id,
                user_fields=["profile_image_url", "name", "username"]
            )
            if response and response.data:
                return {
                    "id": str(response.data.id),
                    "username": response.data.username,
                    "name": response.data.name,
                    "profile_image_url": getattr(response.data, "profile_image_url", None)
                }
        except Exception as e:
            print(f"Error getting user by ID {user_id}: {e}")
        
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, str]]:
        """Get user by username from Twitter API."""
        try:
            response = self.v2_client.get_user(
                username=username,
                user_fields=["profile_image_url", "name", "username"]
            )
            if response and response.data:
                return {
                    "id": str(response.data.id),
                    "username": response.data.username,
                    "name": response.data.name,
                    "profile_image_url": getattr(response.data, "profile_image_url", None)
                }
        except Exception as e:
            print(f"Error getting user by username {username}: {e}")
        
        return None
    
    def download_bytes(self, url: str) -> Optional[bytes]:
        """Download image bytes from URL."""
        try:
            response = requests.get(url, timeout=Config.HTTP_TIMEOUT_SECS)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
            return None
    
    def reply_with_image(self, tweet_id: str, text: str, image_bytes: bytes) -> None:
        """Reply with image using Twitter API."""
        try:
            # Upload media
            media = self.v1_client.media_upload(
                filename="reply.jpg",
                file=image_bytes
            )
            
            # Post reply
            self.v2_client.create_tweet(
                text=text,
                media_ids=[media.media_id],
                in_reply_to_tweet_id=tweet_id
            )
            
            print(f"Successfully replied to tweet {tweet_id}")
        except Exception as e:
            print(f"Error replying to tweet {tweet_id}: {e}")
            raise
