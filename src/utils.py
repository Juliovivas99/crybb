"""
Utility functions for CryBB Maker Bot.
"""
import re
from typing import Optional

def extract_target_after_bot(tweet, bot_handle: str, author_username: str) -> str:
    """
    Choose the first username *immediately after* @bot in tweet.entities.mentions (v2).
    Fallbacks: first non-bot mention -> author_username.
    """
    ents = ((getattr(tweet, "data", {}) or {}).get("entities") or {}).get("mentions") or []
    if not ents:
        return author_username or ""

    bh = bot_handle.lstrip("@").lower()
    bot_positions = [i for i, m in enumerate(ents) if (m.get("username","") or "").lower() == bh]

    if not bot_positions:
        for m in ents:
            u = (m.get("username") or "").lower()
            if u != bh:
                return m["username"]
        return author_username or ""

    first_bot_idx = min(bot_positions)
    if first_bot_idx + 1 < len(ents):
        candidate = ents[first_bot_idx + 1].get("username")
        if candidate and candidate.lower() != bh:
            return candidate

    for m in ents:
        u = (m.get("username") or "").lower()
        if u != bh:
            return m["username"]

    return author_username or ""

def normalize_pfp_url(url: str) -> str:
    """Normalize profile picture URL to higher resolution."""
    if not url:
        return url
    return (url
            .replace("_normal.", "_400x400.")
            .replace("_bigger.", "_400x400.")
            .replace("_mini.", "_400x400."))

def extract_target_username(text: str, bot_handle: str) -> Optional[str]:
    """
    Extract target username from mention text (legacy fallback).
    
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
        return f"Here's your CryBB PFP @{target_username} 🍼"
    else:
        return "Here's your CryBB PFP 🍼"

def format_rate_limit_message() -> str:
    """Format a friendly rate limit message."""
    return "Hey! I'm getting a bit overwhelmed 😅 Please wait a bit before requesting another CryBB PFP!"

def format_error_message() -> str:
    """Format a friendly error message."""
    return "Oops! Something went wrong while processing your request. Please try again later! 🙏"
