"""
Live Twitter client using Tweepy API.
"""
import io
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
            
            bot_id = me.data.id
            
            # Fixed: use snake_case params and include entities expansion
            response = self.v2_client.get_users_mentions(
                id=bot_id,
                since_id=since_id,
                max_results=10,
                expansions=["author_id", "entities.mentions.username"],
                user_fields=["username", "profile_image_url"],
                tweet_fields=["created_at", "entities"]
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
                profile_url = getattr(response.data, "profile_image_url", None)
                return {
                    "id": str(response.data.id),
                    "username": response.data.username,
                    "name": response.data.name,
                    "profile_image_url": profile_url
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
                profile_url = getattr(response.data, "profile_image_url", None)
                return {
                    "id": str(response.data.id),
                    "username": response.data.username,
                    "name": response.data.name,
                    "profile_image_url": profile_url
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
    
    def reply_with_image(self, in_reply_to_tweet_id: str, text: str, image_bytes: bytes) -> None:
        """Reply with image using Twitter API."""
        try:
            print(f"Uploading media: {len(image_bytes)} bytes")
            
            # Fixed: wrap bytes in BytesIO
            buf = io.BytesIO(image_bytes)
            buf.seek(0)

            media = self.v1_client.media_upload(
                filename="crybb.jpg",
                file=buf
            )
            media_id = getattr(media, "media_id", None) or getattr(media, "media_id_string", None)

            # Try both media_ids formats for compatibility
            try:
                self.v2_client.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=in_reply_to_tweet_id,
                    media_ids=[media_id]
                )
            except TypeError:
                self.v2_client.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=in_reply_to_tweet_id,
                    media={"media_ids": [media_id]}
                )
            
            print(f"Successfully replied to tweet {in_reply_to_tweet_id}")
        except Exception as e:
            print(f"Error replying to tweet {in_reply_to_tweet_id}: {e}")
            raise
