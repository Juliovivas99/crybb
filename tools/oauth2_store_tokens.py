#!/usr/bin/env python3
"""
One-time CLI tool to store OAuth 2.0 tokens from .env to credentials.json.
For headless runs where tokens are provided via environment variables.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Ensure repo root on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def main() -> int:
    """Store OAuth 2.0 tokens from environment to credentials file."""
    load_dotenv()
    
    # Get tokens from environment
    access_token = os.getenv("OAUTH2_USER_ACCESS_TOKEN")
    refresh_token = os.getenv("OAUTH2_USER_REFRESH_TOKEN")
    
    if not access_token or not refresh_token:
        print("ERROR: OAUTH2_USER_ACCESS_TOKEN and OAUTH2_USER_REFRESH_TOKEN must be set in .env")
        return 1
    
    # Create credentials directory
    home_dir = os.path.expanduser("~")
    creds_dir = os.path.join(home_dir, ".crybb")
    os.makedirs(creds_dir, exist_ok=True)
    
    # Store tokens
    creds_file = os.path.join(creds_dir, "credentials.json")
    credentials = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": 0,  # Will be updated on first use
        "token_type": "bearer"
    }
    
    try:
        with open(creds_file, 'w') as f:
            json.dump(credentials, f, indent=2)
        
        print(f"SUCCESS: OAuth 2.0 tokens stored in {creds_file}")
        print("Tokens will be automatically refreshed as needed")
        return 0
        
    except Exception as e:
        print(f"ERROR: Failed to store tokens: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

