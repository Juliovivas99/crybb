"""
X API v2 helpers with proper authentication and caching.
Provides clean interface for v2 endpoints with intelligent caching.
"""
import time
import requests
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from requests_oauthlib import OAuth1
from config import Config


@dataclass
class UserInfo:
    """User information with caching."""
    id: str
    username: str
    name: str
    profile_image_url: Optional[str] = None


@dataclass
class RateLimitInfo:
    """Rate limit information."""
    limit: int
    remaining: int
    reset: int


def bearer_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {Config.BEARER_TOKEN}",
        "Content-Type": "application/json",
    }


def oauth1_auth() -> OAuth1:
    return OAuth1(
        Config.API_KEY,
        Config.API_SECRET,
        Config.ACCESS_TOKEN,
        Config.ACCESS_SECRET,
    )


class XAPIv2Client:
    """X API v2 client with intelligent caching and rate limiting."""
    
    def __init__(self):
        """Initialize without OAuth2; use Bearer for reads and OAuth1a for writes."""
        self.base_url = "https://api.twitter.com/2"
        
        # Caching
        self._bot_identity: Optional[Tuple[str, str]] = None
        self._bot_identity_fetched_at: Optional[float] = None
        self._user_cache: Dict[str, UserInfo] = {}
        self._user_cache_ttl = 300  # 5 minutes
        
        # Rate limiting
        self._rate_limits: Dict[str, RateLimitInfo] = {}
    
    def _oauth1(self) -> OAuth1:
        """Create OAuth1 authentication object for v1.1 endpoints."""
        # Guard: all 4 OAuth1 creds must be present
        missing = [name for name, val in [
            ("API_KEY", Config.API_KEY),
            ("API_SECRET", Config.API_SECRET),
            ("ACCESS_TOKEN", Config.ACCESS_TOKEN),
            ("ACCESS_SECRET", Config.ACCESS_SECRET),
        ] if not val]
        if missing:
            raise RuntimeError(f"Missing OAuth1 credentials: {', '.join(missing)}")
        return OAuth1(
            Config.API_KEY,
            Config.API_SECRET,
            Config.ACCESS_TOKEN,
            Config.ACCESS_SECRET
        )
    
    def _capture_rate_limits(self, response: requests.Response, endpoint: str) -> None:
        """Capture rate limit information from response headers."""
        try:
            limit = int(response.headers.get('x-rate-limit-limit', 0))
            remaining = int(response.headers.get('x-rate-limit-remaining', 0))
            reset = int(response.headers.get('x-rate-limit-reset', 0))
            
            if limit > 0:
                self._rate_limits[endpoint] = RateLimitInfo(
                    limit=limit,
                    remaining=remaining,
                    reset=reset
                )
        except (ValueError, TypeError):
            pass
    
    def _log_request(self, auth_type: str, method: str, url: str, 
                    status_code: int, endpoint: str) -> None:
        """Log request with rate limit information."""
        remaining = "N/A"
        reset_time = "N/A"
        
        if endpoint in self._rate_limits:
            rate_info = self._rate_limits[endpoint]
            remaining = rate_info.remaining
            reset_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(rate_info.reset))
        
        print(f"auth={auth_type} {method} {url} status={status_code} remaining={remaining} reset={reset_time}")
    
    def _maybe_sleep(self, endpoint: str) -> None:
        """Sleep until reset+5s if remaining is low (default threshold 2)."""
        self.maybe_sleep(endpoint, min_remaining=2)

    def maybe_sleep(self, endpoint: str, min_remaining: int = 2) -> None:
        if endpoint not in self._rate_limits:
            return
        rate_info = self._rate_limits[endpoint]
        if rate_info.remaining < min_remaining:
            now = time.time()
            wait = max(0.0, rate_info.reset - now) + 5.0
            print(f"⚠️  Rate limit low for {endpoint} ({rate_info.remaining}/{rate_info.limit}), sleeping {wait:.1f}s until reset+5s")
            time.sleep(wait)
    
    def get_me(self) -> Tuple[str, str]:
        """Get bot identity with indefinite caching."""
        # Return cached if available
        if self._bot_identity:
            return self._bot_identity
        
        try:
            url = "https://api.twitter.com/1.1/account/verify_credentials.json"
            response = requests.get(url, auth=self._oauth1(), timeout=30)
            self._capture_rate_limits(response, 'account/verify_credentials')
            self._log_request('OAuth1a', 'GET', url, response.status_code, 'account/verify_credentials')
            
            response.raise_for_status()
            data = response.json()
            
            bot_id = data['id_str']
            bot_username = data['screen_name']
            
            # Cache the result indefinitely
            self._bot_identity = (bot_id, bot_username)
            
            print(f"Bot identity cached via OAuth1a: @{bot_username} (ID: {bot_id})")
            return self._bot_identity
            
        except Exception as e:
            print(f"OAuth1a identity failed: {e}")
        
        # Final fallback
        return "123456789", "crybbmaker"
    
    def get_user_by_username(self, username: str) -> Optional[UserInfo]:
        """Get user by username with 5-minute caching."""
        # Check cache first
        for cached_user in self._user_cache.values():
            if cached_user.username == username:
                return cached_user
        
        try:
            url = f"{self.base_url}/users/by/username/{username}"
            params = {
                'user.fields': 'id,username,name,profile_image_url'
            }
            
            response = requests.get(url, headers=bearer_headers(), params=params, timeout=30)
            self._capture_rate_limits(response, 'users/by/username')
            self._log_request('Bearer', 'GET', url, response.status_code, 'users/by/username')
            
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
                self._user_cache[user_info.id] = user_info
                return user_info
            
        except Exception as e:
            print(f"Error getting user by username {username}: {e}")
        
        return None
    
    def get_mentions(self, user_id: str, since_id: Optional[str] = None, 
                    max_results: int = 100) -> List[Dict[str, Any]] | Dict[str, Any]:
        """Get mentions with comprehensive expansions."""
        try:
            url = f"{self.base_url}/users/{user_id}/mentions"
            params = {
                'max_results': max_results,
                'expansions': 'author_id,entities.mentions.username',
                'user.fields': 'id,username,name,profile_image_url',
                'tweet.fields': 'created_at,entities,author_id'
            }
            
            if since_id:
                params['since_id'] = since_id
            
            response = requests.get(url, headers=bearer_headers(), params=params, timeout=30)
            self._capture_rate_limits(response, 'users/mentions')
            self._log_request('Bearer', 'GET', url, response.status_code, 'users/mentions')

            if response.status_code == 429:
                # Rate limited: sleep until reset + 5s and return marker
                rate = self._rate_limits.get('users/mentions')
                if rate:
                    now = time.time()
                    wait = max(0.0, rate.reset - now) + 5.0
                    print(f"Mentions rate-limited; sleeping {wait:.1f}s until reset+5s")
                    time.sleep(wait)
                return {"rate_limited": True, "route": "users/mentions"}

            response.raise_for_status()
            data = response.json()
            
            # Process mentions with expanded user data
            mentions = []
            if 'data' in data:
                # Create user lookup from expansions
                users_by_id = {}
                if 'includes' in data and 'users' in data['includes']:
                    for user in data['includes']['users']:
                        users_by_id[user['id']] = {
                            'id': user['id'],
                            'username': user['username'],
                            'name': user['name'],
                            'profile_image_url': user.get('profile_image_url')
                        }
                
                # Process mentions and attach user data
                for mention in data['data']:
                    mention_data = mention.copy()
                    
                    # Attach author info
                    if 'author_id' in mention and mention['author_id'] in users_by_id:
                        mention_data['author'] = users_by_id[mention['author_id']]
                    
                    # Attach mentioned users
                    if 'entities' in mention and 'mentions' in mention['entities']:
                        mentioned_users = {}
                        for mention_entity in mention['entities']['mentions']:
                            username = mention_entity.get('username')
                            if username:
                                for user_id, user_data in users_by_id.items():
                                    if user_data['username'] == username:
                                        mentioned_users[username] = user_data
                                        break
                        mention_data['mentioned_users'] = mentioned_users
                    
                    # Cache user data
                    if 'author' in mention_data:
                        user_info = UserInfo(
                            id=mention_data['author']['id'],
                            username=mention_data['author']['username'],
                            name=mention_data['author']['name'],
                            profile_image_url=mention_data['author'].get('profile_image_url')
                        )
                        self._user_cache[user_info.id] = user_info
                    
                    mentions.append(mention_data)
            
            print(f"Retrieved {len(mentions)} mentions with expanded user data")
            self._maybe_sleep('users/mentions')
            
            return mentions
            
        except Exception as e:
            print(f"Error getting mentions: {e}")
            return []
    
    def media_upload(self, image_bytes: bytes, mime: str = "image/jpeg") -> str:
        """
        Upload media using v1.1 + OAuth1a; return media_id_string.
        """
        try:
            print(f"Uploading media: {len(image_bytes)} bytes")
            
            url = "https://upload.twitter.com/1.1/media/upload.json"
            files = {"media": ("crybb.jpg", image_bytes, mime)}
            
            # Use OAuth1a for v1.1 media upload endpoint
            resp = requests.post(url, files=files, auth=self._oauth1(), timeout=30)
            self._capture_rate_limits(resp, 'media/upload')
            self._log_request('OAuth1a', 'POST', url, resp.status_code, 'media/upload')
            
            if not resp.ok:
                # Better error visibility
                raise RuntimeError(f"Media upload failed ({resp.status_code}): {resp.text}")

            data = resp.json()
            mid = data.get("media_id_string")
            if not mid:
                raise RuntimeError(f"Upload OK but missing media_id_string: {data}")
            
            print(f"Media uploaded successfully: {mid}")
            return mid
            
        except Exception as e:
            print(f"Error uploading media: {e}")
            raise
    
    def create_reply(self, text: str, in_reply_to_tweet_id: str, 
                    media_ids: Optional[List[str]] = None) -> Optional[str]:
        """Create a reply tweet using v2 API."""
        try:
            url = f"{self.base_url}/tweets"
            data = {
                'text': text,
                'reply': {
                    'in_reply_to_tweet_id': in_reply_to_tweet_id
                }
            }
            
            if media_ids:
                data['media'] = {
                    'media_ids': media_ids
                }
            
            response = requests.post(url, json=data, auth=self._oauth1(), timeout=30)
            self._capture_rate_limits(response, 'tweets')
            self._log_request('OAuth1a', 'POST', url, response.status_code, 'tweets')
            
            response.raise_for_status()
            result = response.json()
            
            if 'data' in result and 'id' in result['data']:
                tweet_id = result['data']['id']
                print(f"Tweet created successfully: {tweet_id}")
                return tweet_id
            
        except Exception as e:
            print(f"Error creating tweet: {e}")
        
        return None
    
    def reply_with_image(self, in_reply_to_tweet_id: str, text: str, image_bytes: bytes) -> None:
        """Reply to a tweet with an image."""
        try:
            # Upload media first
            media_id = self.media_upload(image_bytes)
            
            # Create reply with media
            tweet_id = self.create_reply(
                text=text,
                in_reply_to_tweet_id=in_reply_to_tweet_id,
                media_ids=[media_id]
            )
            
            if tweet_id:
                print(f"Successfully replied to tweet {in_reply_to_tweet_id} with image")
            else:
                print("Failed to create reply tweet")
                
        except Exception as e:
            print(f"Error replying to tweet {in_reply_to_tweet_id}: {e}")
            raise
    
    def get_rate_limit_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current rate limit status."""
        status = {}
        for endpoint, rate_info in self._rate_limits.items():
            status[endpoint] = {
                'limit': rate_info.limit,
                'remaining': rate_info.remaining,
                'reset': rate_info.reset,
                'reset_time': time.ctime(rate_info.reset)
            }
        return status

    # Sleeper helpers
    def get_user_tweets(self, user_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent tweets for a user via v2 (Bearer)."""
        try:
            url = f"{self.base_url}/users/{user_id}/tweets"
            params = {
                'max_results': str(max(5, min(max_results, 100))),
                'tweet.fields': 'public_metrics,created_at'
            }
            r = requests.get(url, headers=bearer_headers(), params=params, timeout=30)
            self._capture_rate_limits(r, 'users/tweets')
            self._log_request('Bearer', 'GET', url, r.status_code, 'users/tweets')
            r.raise_for_status()
            return r.json().get('data', []) or []
        except Exception as e:
            print(f"Error fetching user tweets for {user_id}: {e}")
            return []

    def retweet_v11(self, tweet_id: str) -> Dict[str, Any] | Dict[str, Any]:
        """Retweet via v1.1 statuses/retweet/<id>.json with OAuth1a."""
        url = f"https://api.twitter.com/1.1/statuses/retweet/{tweet_id}.json"
        r = requests.post(url, auth=self._oauth1(), timeout=30)
        self._capture_rate_limits(r, 'statuses/retweet')
        self._log_request('OAuth1a', 'POST', url, r.status_code, 'statuses/retweet')
        if r.status_code == 429:
            return {"rate_limited": True, "route": "statuses/retweet"}
        r.raise_for_status()
        return r.json()
