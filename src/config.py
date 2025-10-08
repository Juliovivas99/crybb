"""
Configuration module for CryBB Maker Bot.
Handles environment variables and constants.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class with validation."""
    
    # Twitter API credentials
    CLIENT_ID: str = os.getenv("CLIENT_ID", "")
    CLIENT_SECRET: str = os.getenv("CLIENT_SECRET", "")
    API_KEY: str = os.getenv("API_KEY", "")
    API_SECRET: str = os.getenv("API_SECRET", "")
    ACCESS_TOKEN: str = os.getenv("ACCESS_TOKEN", "")
    ACCESS_SECRET: str = os.getenv("ACCESS_SECRET", "")
    BEARER_TOKEN: str = os.getenv("BEARER_TOKEN", "")
    
    # Bot configuration
    BOT_HANDLE: str = os.getenv("BOT_HANDLE", "crybbmaker")
    POLL_SECONDS: int = int(os.getenv("POLL_SECONDS", "30"))
    WATERMARK_TEXT: Optional[str] = os.getenv("WATERMARK_TEXT", "made by @crybbmaker")
    PORT: int = int(os.getenv("PORT", "8000"))
    TWITTER_MODE: str = os.getenv("TWITTER_MODE", "live")  # live | dryrun | mock
    OUTBOX_DIR: str = os.getenv("OUTBOX_DIR", "outbox")
    FIXTURES_DIR: str = os.getenv("FIXTURES_DIR", "fixtures")
    
    # Rate limiting
    RATE_LIMIT_PER_HOUR: int = 5
    
    # Image processing
    JPEG_QUALITY: int = 90
    # HTTP
    HTTP_TIMEOUT_SECS: int = int(os.getenv("HTTP_TIMEOUT_SECS", "10"))

    # AI / Replicate
    REPLICATE_API_TOKEN: str = os.getenv("REPLICATE_API_TOKEN", "")
    REPLICATE_MODEL: str = os.getenv("REPLICATE_MODEL", "google/nano-banana")
    REPLICATE_TIMEOUT_SECS: int = int(os.getenv("REPLICATE_TIMEOUT_SECS", "120"))
    REPLICATE_POLL_INTERVAL_SECS: float = float(os.getenv("REPLICATE_POLL_INTERVAL_SECS", "2"))
    AI_MAX_CONCURRENCY: int = int(os.getenv("AI_MAX_CONCURRENCY", "2"))
    AI_MAX_ATTEMPTS: int = int(os.getenv("AI_MAX_ATTEMPTS", "2"))

    # Public URL of the constant style anchor (crybb.jpeg)
    CRYBB_STYLE_URL: Optional[str] = os.getenv("CRYBB_STYLE_URL")

    # Pipeline mode
    IMAGE_PIPELINE: str = os.getenv("IMAGE_PIPELINE", "ai")  # ai | placeholder
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        required_creds = [
            ("CLIENT_ID", cls.CLIENT_ID),
            ("CLIENT_SECRET", cls.CLIENT_SECRET),
            ("API_KEY", cls.API_KEY),
            ("API_SECRET", cls.API_SECRET),
            ("ACCESS_TOKEN", cls.ACCESS_TOKEN),
            ("ACCESS_SECRET", cls.ACCESS_SECRET),
            ("BEARER_TOKEN", cls.BEARER_TOKEN),
        ]
        
        missing = [name for name, value in required_creds if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Additional validation for AI pipeline
        if (cls.IMAGE_PIPELINE or "ai").lower() == "ai":
            ai_missing = []
            if not cls.REPLICATE_API_TOKEN:
                ai_missing.append("REPLICATE_API_TOKEN")
            if not cls.CRYBB_STYLE_URL:
                ai_missing.append("CRYBB_STYLE_URL")
            if ai_missing:
                raise ValueError(
                    "IMAGE_PIPELINE=ai requires: " + ", ".join(ai_missing)
                )
    
    @classmethod
    def get_bot_handle_clean(cls) -> str:
        """Get bot handle without @ prefix."""
        return cls.BOT_HANDLE.lstrip("@")

# Validate configuration on import (skip during testing)
if not os.getenv("SKIP_CONFIG_VALIDATION"):
    Config.validate()
