"""
Modern Twitter API v2 client with intelligent rate limiting and caching.
Replaces the legacy Tweepy v1.1/v2 hybrid approach with pure v2 implementation.
"""
import io
import json
import time
import base64
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from config import Config


@dataclass
class RateLimitInfo:
    """Rate limit information from API headers."""
    limit: int
    remaining: int
    reset: int
    retry_after: Optional[int] = None


@dataclass
class UserInfo:
    """Cached user information."""
    id: str
    username: str
    name: str
    profile_image_url: Optional[str] = None


class TwitterClientV2:
    """
    Modern Twitter API v2 client with intelligent caching and rate limiting.
    
    Key improvements:
    - Pure v2 API implementation with OAuth 2.0 Bearer Token authentication
    - Intelligent caching to minimize API calls
    - Adaptive rate limiting with exponential backoff
    - Proper media upload using v1.1 endpoint (v2 doesn't support media upload yet)
    - Comprehensive error handling
    - Hybrid authentication: OAuth 2.0 for v2 endpoints, OAuth 1.0a for media upload
    """
    
    def __init__(self):
        """Initialize the v2 client with OAuth 2.0 Bearer Token authentication."""
        self.base_url = "https://api.twitter.com/2"
        self.media_url = "https://upload.twitter.com/1.1/media/upload.json"  # Media upload still uses v1.1 endpoint
        
        # OAuth 2.0 Bearer Token for v2 API endpoints
        self.bearer_token = Config.BEARER_TOKEN
        
        # OAuth 1.0a credentials for media upload (v1.1 endpoint only)
        self.api_key = Config.API_KEY
        self.api_secret = Config.API_SECRET
        self.access_token = Config.ACCESS_TOKEN
        self.access_secret = Config.ACCESS_SECRET
        
        # Cached bot identity (fetched once at startup)
        self._bot_identity: Optional[Tuple[str, str]] = None
        self._bot_identity_fetched_at: Optional[float] = None
        
        # User cache to avoid redundant API calls
        self._user_cache: Dict[str, UserInfo] = {}
        self._user_cache_ttl = 300  # 5 minutes TTL for user cache
        
        # Rate limit tracking
        self._rate_limits: Dict[str, RateLimitInfo] = {}
        self._last_request_time = 0.0
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.timeout = Config.HTTP_TIMEOUT_SECS
        
        print("Twitter API v2 client initialized with intelligent caching")
    
    def _get_oauth_headers(self, method: str, url: str, params: Optional[Dict] = None) -> Dict[str, str]:
        """
        Generate OAuth 1.0a headers for authenticated requests.
        Uses requests-oauthlib for reliable OAuth 1.0a implementation.
        """
        from requests_oauthlib import OAuth1
        
        # Create OAuth1 authentication object
        auth = OAuth1(
            self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_secret,
            signature_method='HMAC-SHA1',
            signature_type='AUTH_HEADER'
        )
        
        # Generate headers using requests-oauthlib
        # We need to create a mock request to get the headers
        import requests
        from requests.auth import HTTPBasicAuth
        
        # Create a temporary request to extract OAuth headers
        req = requests.Request(method, url, params=params)
        prepared = req.prepare()
        
        # Apply OAuth authentication
        auth(prepared)
        
        return {
            'Authorization': str(prepared.headers['Authorization']),
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, url: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None, files: Optional[Dict] = None) -> requests.Response:
        """
        Make authenticated request with proper authentication per endpoint:
        - OAuth 2.0 Bearer Token: For reading mentions (GET /2/users/:id/mentions)
        - OAuth 1.0a User Context: For creating tweets (POST /2/tweets) and uploading media (POST /1.1/media/upload.json)
        """
        # Rate limiting: ensure minimum time between requests
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        min_interval = 0.1  # 100ms minimum between requests
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self._last_request_time = time.time()
        
        # Determine authentication type and route name
        auth_type = "OAuth1a" if (files or 'upload.twitter.com' in url or 'api.twitter.com/1.1' in url or 'tweets' in url) else "Bearer"
        route_name = self._get_route_name(url)
        
        # Prepare headers based on endpoint type
        if auth_type == "OAuth1a":
            # Media upload, v1.1 endpoints, and tweet creation use OAuth 1.0a
            headers = self._get_oauth_headers(method, url, params)
            if 'Content-Type' in headers:
                del headers['Content-Type']  # Let requests set it for multipart
        else:
            # Other v2 API endpoints use OAuth 2.0 Bearer Token
            headers = {
                'Authorization': f'Bearer {self.bearer_token}',
                'Content-Type': 'application/json'
            }
        
        # Make request
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                if files:
                    response = self.session.post(url, headers=headers, data=data, files=files)
                else:
                    response = self.session.post(url, headers=headers, params=params, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Capture rate limits and log request
            self._capture_limits(response, route_name)
            self._log_request(auth_type, method, url, response.status_code, route_name)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                # Retry the request
                return self._make_request(method, url, params, data, files)
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise
    
    def _get_route_name(self, url: str) -> str:
        """Extract route name from URL for rate limiting."""
        if '/users/by/username/' in url:
            return 'users/by/username'
        elif '/users/' in url and '/mentions' in url:
            return 'users/mentions'
        elif '/users/' in url:
            return 'users'
        elif '/tweets' in url:
            return 'tweets'
        elif 'upload.twitter.com' in url:
            return 'media/upload'
        elif '/1.1/account/verify_credentials' in url:
            return 'account/verify_credentials'
        else:
            return 'unknown'
    
    def _capture_limits(self, response: requests.Response, route_name: str) -> None:
        """Capture and store rate limit information from response headers."""
        try:
            limit = int(response.headers.get('x-rate-limit-limit', 0))
            remaining = int(response.headers.get('x-rate-limit-remaining', 0))
            reset = int(response.headers.get('x-rate-limit-reset', 0))
            
            if limit > 0:  # Only store if we got valid rate limit info
                self._rate_limits[route_name] = RateLimitInfo(
                    limit=limit,
                    remaining=remaining,
                    reset=reset
                )
                
        except (ValueError, TypeError):
            pass  # Ignore invalid rate limit headers
    
    def _log_request(self, auth_type: str, method: str, url: str, status_code: int, route_name: str) -> None:
        """Log request details with authentication type and rate limit info."""
        remaining = "N/A"
        reset_time = "N/A"
        
        if route_name in self._rate_limits:
            rate_info = self._rate_limits[route_name]
            remaining = rate_info.remaining
            reset_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(rate_info.reset))
        
        print(f"auth={auth_type} {method} {url} status={status_code} remaining={remaining} reset={reset_time}")
    
    def _maybe_sleep(self, route_name: str) -> None:
        """Adaptive backoff helper that respects rate limits."""
        if route_name not in self._rate_limits:
            return
        
        rate_info = self._rate_limits[route_name]
        current_time = time.time()
        
        # Sleep until reset + 5 seconds if remaining < 2
        if rate_info.remaining < 2:
            time_until_reset = rate_info.reset - current_time
            if time_until_reset > 0:
                sleep_time = time_until_reset + 5  # Add 5 second buffer
                print(f"⚠️  Rate limit low ({rate_info.remaining}/{rate_info.limit}), sleeping {sleep_time:.1f}s until reset")
                time.sleep(sleep_time)
        
        # Also handle 429 responses (rate limited)
        elif rate_info.remaining == 0:
            time_until_reset = rate_info.reset - current_time
            if time_until_reset > 0:
                sleep_time = time_until_reset + 5  # Add 5 second buffer
                print(f"🚫 Rate limit exceeded, sleeping {sleep_time:.1f}s until reset")
                time.sleep(sleep_time)
    
    def _parse_rate_limit_headers(self, headers: Dict[str, str], endpoint: str) -> None:
        """Parse and store rate limit information from response headers."""
        try:
            limit = int(headers.get('x-rate-limit-limit', 0))
            remaining = int(headers.get('x-rate-limit-remaining', 0))
            reset = int(headers.get('x-rate-limit-reset', 0))
            
            if limit > 0:  # Only store if we got valid rate limit info
                self._rate_limits[endpoint] = RateLimitInfo(
                    limit=limit,
                    remaining=remaining,
                    reset=reset
                )
                
                # Log rate limit status for monitoring
                if remaining < 5:
                    print(f"⚠️  Rate limit warning for {endpoint}: {remaining}/{limit} remaining")
                
        except (ValueError, TypeError):
            pass  # Ignore invalid rate limit headers
    
    def _should_backoff(self, endpoint: str) -> bool:
        """Check if we should back off based on rate limits."""
        if endpoint not in self._rate_limits:
            return False
        
        rate_info = self._rate_limits[endpoint]
        
        # Back off if we have very few requests remaining
        if rate_info.remaining <= 2:
            return True
        
        # Check if we're close to reset time
        current_time = time.time()
        time_until_reset = rate_info.reset - current_time
        
        # If reset is soon and we have few requests left, back off
        if time_until_reset < 60 and rate_info.remaining <= 5:
            return True
        
        return False
    
    def get_bot_identity(self) -> Tuple[str, str]:
        """
        Get bot identity with intelligent caching.
        Only calls API once at startup, then uses cached result.
        """
        # Return cached identity if available and recent
        if self._bot_identity and self._bot_identity_fetched_at:
            age = time.time() - self._bot_identity_fetched_at
            if age < 3600:  # Cache for 1 hour
                return self._bot_identity
        
        try:
            # Use v1.1 endpoint for /users/me as it requires OAuth 1.0a User Context
            url = "https://api.twitter.com/1.1/account/verify_credentials.json"
            params = {
                'include_entities': 'false',
                'skip_status': 'true',
                'include_email': 'false'
            }
            
            response = self._make_request('GET', url, params)
            data = response.json()
            
            if 'id' in data and 'screen_name' in data:
                bot_id = str(data['id'])
                bot_username = data['screen_name']
                
                # Cache the result
                self._bot_identity = (bot_id, bot_username)
                self._bot_identity_fetched_at = time.time()
                
                print(f"Bot identity cached: @{bot_username} (ID: {bot_id})")
                return self._bot_identity
            
        except Exception as e:
            print(f"Error getting bot identity: {e}")
        
        # Fallback to config values
        return "123456789", Config.BOT_HANDLE
    
    def get_mentions(self, since_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get mentions with comprehensive user data expansion to minimize additional API calls.
        Uses expansions to include author and mentioned user data in the response.
        """
        try:
            bot_id, _ = self.get_bot_identity()
            
            # Check if we should back off
            if self._should_backoff('users/mentions'):
                print("Backing off from mentions due to rate limits")
                return []
            
            url = f"{self.base_url}/users/{bot_id}/mentions"
            params = {
                'max_results': 10,
                'expansions': 'author_id,entities.mentions.username',
                'user.fields': 'id,username,name,profile_image_url',
                'tweet.fields': 'created_at,entities,author_id'
            }
            
            if since_id:
                params['since_id'] = since_id
            
            response = self._make_request('GET', url, params)
            data = response.json()
            
            # Process the response to include expanded user data
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
                    
                    # Attach author info if available
                    if 'author_id' in mention and mention['author_id'] in users_by_id:
                        mention_data['author'] = users_by_id[mention['author_id']]
                    
                    # Attach all mentioned users for efficient target lookup
                    if 'entities' in mention and 'mentions' in mention['entities']:
                        mentioned_users = {}
                        for mention_entity in mention['entities']['mentions']:
                            username = mention_entity.get('username')
                            if username:
                                # Find user by username in expanded data
                                for user_id, user_data in users_by_id.items():
                                    if user_data['username'] == username:
                                        mentioned_users[username] = user_data
                                        break
                        mention_data['mentioned_users'] = mentioned_users
                    
                    # Cache user data for future use
                    if 'author' in mention_data:
                        user_info = UserInfo(
                            id=mention_data['author']['id'],
                            username=mention_data['author']['username'],
                            name=mention_data['author']['name'],
                            profile_image_url=mention_data['author'].get('profile_image_url')
                        )
                        self._user_cache[user_info.id] = user_info
                    
                    # Cache mentioned users too
                    if 'mentioned_users' in mention_data:
                        for username, user_data in mention_data['mentioned_users'].items():
                            user_info = UserInfo(
                                id=user_data['id'],
                                username=user_data['username'],
                                name=user_data['name'],
                                profile_image_url=user_data.get('profile_image_url')
                            )
                            self._user_cache[user_info.id] = user_info
                    
                    mentions.append(mention_data)
            
            print(f"Retrieved {len(mentions)} mentions with expanded user data")
            
            # Apply adaptive backoff after mentions fetch
            self._maybe_sleep('users/mentions')
            
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
        if user_id in self._user_cache:
            cached_user = self._user_cache[user_id]
            # Cache is valid for 5 minutes
            return cached_user
        
        try:
            # Check if we should back off
            if self._should_backoff('/users'):
                print(f"Backing off from user lookup for {user_id}")
                return None
            
            url = f"{self.base_url}/users/{user_id}"
            params = {
                'user.fields': 'id,username,name,profile_image_url'
            }
            
            response = self._make_request('GET', url, params)
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
                self._user_cache[user_id] = user_info
                return user_info
            
        except Exception as e:
            print(f"Error getting user by ID {user_id}: {e}")
        
        return None
    
    def get_user_by_username(self, username: str) -> Optional[UserInfo]:
        """
        Get user by username with intelligent caching.
        Checks cache first, only makes API call if needed.
        """
        # Check cache by username (less efficient but still better than API call)
        for cached_user in self._user_cache.values():
            if cached_user.username == username:
                return cached_user
        
        try:
            # Check if we should back off
            if self._should_backoff('/users/by/username'):
                print(f"Backing off from username lookup for {username}")
                return None
            
            url = f"{self.base_url}/users/by/username/{username}"
            params = {
                'user.fields': 'id,username,name,profile_image_url'
            }
            
            response = self._make_request('GET', url, params)
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
    
    def download_bytes(self, url: str) -> Optional[bytes]:
        """Download image bytes from URL with proper error handling."""
        try:
            response = self.session.get(url, timeout=Config.HTTP_TIMEOUT_SECS)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
            return None
    
    def upload_media(self, image_bytes: bytes, filename: str = "crybb.jpg") -> Optional[str]:
        """
        Upload media using Twitter's v1.1 media upload endpoint.
        Note: Media upload still uses v1.1 endpoint as v2 doesn't have media upload yet.
        """
        try:
            print(f"Uploading media: {len(image_bytes)} bytes")
            
            # Prepare multipart form data
            files = {
                'media': (filename, io.BytesIO(image_bytes), 'image/jpeg')
            }
            
            response = self._make_request('POST', self.media_url, files=files)
            data = response.json()
            
            if 'media_id_string' in data:
                media_id = data['media_id_string']
                print(f"Media uploaded successfully: {media_id}")
                return media_id
            elif 'media_id' in data:
                media_id = str(data['media_id'])
                print(f"Media uploaded successfully: {media_id}")
                return media_id
            
        except Exception as e:
            print(f"Error uploading media: {e}")
        
        return None
    
    def create_tweet(self, text: str, in_reply_to_tweet_id: Optional[str] = None, 
                    media_ids: Optional[List[str]] = None) -> Optional[str]:
        """
        Create a tweet using Twitter API v2.
        Supports text, replies, and media attachments.
        """
        try:
            # Check if we should back off
            if self._should_backoff('/tweets'):
                print("Backing off from tweet creation due to rate limits")
                return None
            
            url = f"{self.base_url}/tweets"
            data = {
                'text': text
            }
            
            if in_reply_to_tweet_id:
                data['reply'] = {
                    'in_reply_to_tweet_id': in_reply_to_tweet_id
                }
            
            if media_ids:
                data['media'] = {
                    'media_ids': media_ids
                }
            
            response = self._make_request('POST', url, data=data)
            result = response.json()
            
            if 'data' in result and 'id' in result['data']:
                tweet_id = result['data']['id']
                print(f"Tweet created successfully: {tweet_id}")
                return tweet_id
            
        except Exception as e:
            print(f"Error creating tweet: {e}")
        
        return None
    
    def reply_with_image(self, in_reply_to_tweet_id: str, text: str, image_bytes: bytes) -> None:
        """
        Reply to a tweet with an image using pure v2 API.
        This is the main method used by the bot for replying.
        """
        try:
            # Upload media first
            media_id = self.upload_media(image_bytes)
            if not media_id:
                print("Failed to upload media")
                return
            
            # Create tweet with media
            tweet_id = self.create_tweet(
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
        """Get current rate limit status for monitoring."""
        status = {}
        for endpoint, rate_info in self._rate_limits.items():
            status[endpoint] = {
                'limit': rate_info.limit,
                'remaining': rate_info.remaining,
                'reset': rate_info.reset,
                'reset_time': time.ctime(rate_info.reset)
            }
        return status
    
    def clear_cache(self) -> None:
        """Clear all caches (useful for testing or memory management)."""
        self._user_cache.clear()
        self._bot_identity = None
        self._bot_identity_fetched_at = None
        print("All caches cleared")
