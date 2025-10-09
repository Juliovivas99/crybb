"""
Utility functions for CryBB Maker Bot.
"""
import re
from typing import Optional

def extract_target_after_bot(tweet_data: dict, bot_handle: str, author_username: str) -> str:
    """
    Choose the first username *immediately after* @bot in tweet.entities.mentions (v2).
    Fallbacks: first non-bot mention -> author_username.
    
    Args:
        tweet_data: Tweet data dict from v2 API
        bot_handle: Bot handle (with or without @)
        author_username: Fallback username if no target found
    
    Returns:
        Target username (without @)
    """
    # Extract entities from tweet data
    entities = tweet_data.get("entities", {})
    mentions = entities.get("mentions", [])
    
    if not mentions:
        return author_username or ""
    
    # Clean bot handle
    bh = bot_handle.lstrip("@").lower()
    
    # Find bot positions in mentions
    bot_positions = [i for i, m in enumerate(mentions) if (m.get("username", "") or "").lower() == bh]
    
    if not bot_positions:
        # No bot mention found, return first non-bot mention
        for m in mentions:
            u = (m.get("username") or "").lower()
            if u != bh:
                return m["username"]
        return author_username or ""
    
    # Find first mention after bot
    first_bot_idx = min(bot_positions)
    if first_bot_idx + 1 < len(mentions):
        candidate = mentions[first_bot_idx + 1].get("username")
        if candidate and candidate.lower() != bh:
            return candidate
    
    # Fallback: return first non-bot mention
    for m in mentions:
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
