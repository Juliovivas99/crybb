"""
OAuth 2.0 authentication for X API v2.
Provides BearerSession for reads and UserSession for writes with token refresh.
"""
import json
import os
import time
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass
from config import Config


@dataclass
class TokenInfo:
    """OAuth 2.0 token information."""
    access_token: str
    refresh_token: str
    expires_at: float
    token_type: str = "bearer"


class BearerSession:
    """Session with OAuth 2.0 Bearer Token for read operations."""
    
    def __init__(self, bearer_token: str):
        """Initialize with bearer token."""
        self.bearer_token = bearer_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json'
        })
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Make GET request with bearer token."""
        return self.session.get(url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """Make POST request with bearer token."""
        return self.session.post(url, **kwargs)


class UserSession:
    """Session with OAuth 2.0 user context for write operations."""
    
    def __init__(self, client_id: str, client_secret: str, 
                 access_token: str, refresh_token: str, token_url: str):
        """Initialize with OAuth 2.0 credentials."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.session = requests.Session()
        
        # Load tokens from storage or use provided ones
        self.tokens = self._load_tokens(access_token, refresh_token)
        self._update_session_headers()
    
    def _load_tokens(self, access_token: str, refresh_token: str) -> TokenInfo:
        """Load tokens from storage or use provided ones."""
        storage_path = self._get_storage_path()
        
        if os.path.exists(storage_path):
            try:
                with open(storage_path, 'r') as f:
                    data = json.load(f)
                    return TokenInfo(
                        access_token=data['access_token'],
                        refresh_token=data['refresh_token'],
                        expires_at=data.get('expires_at', time.time() + 3600),
                        token_type=data.get('token_type', 'bearer')
                    )
            except Exception as e:
                print(f"Error loading tokens from storage: {e}")
        
        # Use provided tokens
        return TokenInfo(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=time.time() + 3600  # Assume 1 hour expiry
        )
    
    def _save_tokens(self) -> None:
        """Save tokens to storage."""
        storage_path = self._get_storage_path()
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        try:
            with open(storage_path, 'w') as f:
                json.dump({
                    'access_token': self.tokens.access_token,
                    'refresh_token': self.tokens.refresh_token,
                    'expires_at': self.tokens.expires_at,
                    'token_type': self.tokens.token_type
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving tokens to storage: {e}")
    
    def _get_storage_path(self) -> str:
        """Get token storage path."""
        home_dir = os.path.expanduser("~")
        return os.path.join(home_dir, ".crybb", "credentials.json")
    
    def _update_session_headers(self) -> None:
        """Update session headers with current access token."""
        self.session.headers.update({
            'Authorization': f'Bearer {self.tokens.access_token}',
            'Content-Type': 'application/json'
        })
    
    def _refresh_token(self) -> bool:
        """Refresh access token using refresh token."""
        try:
            print("Refreshing OAuth 2.0 access token...")
            
            # Prepare refresh request
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.tokens.refresh_token,
                'client_id': self.client_id
            }
            
            # Make refresh request
            response = requests.post(
                self.token_url,
                data=data,
                auth=(self.client_id, self.client_secret),
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Update tokens
                self.tokens.access_token = token_data['access_token']
                self.tokens.refresh_token = token_data.get('refresh_token', self.tokens.refresh_token)
                self.tokens.expires_at = time.time() + token_data.get('expires_in', 3600)
                self.tokens.token_type = token_data.get('token_type', 'bearer')
                
                # Update session headers
                self._update_session_headers()
                
                # Save to storage
                self._save_tokens()
                
                print("Token refreshed successfully")
                return True
            else:
                print(f"Token refresh failed: {response.status_code} {response.text}")
                return False
                
        except Exception as e:
            print(f"Error refreshing token: {e}")
            return False
    
    def _ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token."""
        # Check if token is expired (with 5 minute buffer)
        if time.time() >= self.tokens.expires_at - 300:
            return self._refresh_token()
        return True
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Make GET request with user context."""
        if not self._ensure_valid_token():
            raise Exception("Failed to obtain valid access token")
        return self.session.get(url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """Make POST request with user context."""
        if not self._ensure_valid_token():
            raise Exception("Failed to obtain valid access token")
        return self.session.post(url, **kwargs)


def create_bearer_session() -> BearerSession:
    """Create BearerSession for read operations."""
    return BearerSession(Config.BEARER_TOKEN)


def create_user_session() -> UserSession:
    """Create UserSession for write operations."""
    return UserSession(
        client_id=Config.CLIENT_ID,
        client_secret=Config.CLIENT_SECRET,
        access_token=Config.OAUTH2_USER_ACCESS_TOKEN,
        refresh_token=Config.OAUTH2_USER_REFRESH_TOKEN,
        token_url=Config.OAUTH2_TOKEN_URL
    )
