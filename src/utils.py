"""
Utility functions for CryBB Maker Bot.
"""
import re
from typing import Optional

def extract_target_username(text: str, bot_handle: str) -> Optional[str]:
    """
    Extract target username from mention text.
    
    Args:
        text: The mention text
        bot_handle: The bot's handle (without @)
    
    Returns:
        Target username (without @) or None if no target found
    """
    # Clean bot handle
    bot_handle = bot_handle.lstrip("@").lower()
    
    # Find all @mentions in the text
    mentions = re.findall(r'@(\w+)', text.lower())
    
    # Filter out the bot handle
    targets = [mention for mention in mentions if mention != bot_handle]
    
    # Return the first target found, or None
    return targets[0] if targets else None

def format_friendly_message(target_username: Optional[str] = None) -> str:
    """Format a friendly reply message."""
    if target_username:
        return f"Here's your CryBB PFP @{target_username} 🔥"
    else:
        return "Here's your CryBB PFP 🔥"

def format_rate_limit_message() -> str:
    """Format a friendly rate limit message."""
    return "Hey! I'm getting a bit overwhelmed 😅 Please wait a bit before requesting another CryBB PFP!"

def format_error_message() -> str:
    """Format a friendly error message."""
    return "Oops! Something went wrong while processing your request. Please try again later! 🙏"
