"""
Utility functions for CryBB Maker Bot.
"""
import re
from typing import Optional, Dict, Any, List, Set, Tuple


def _build_excluded_usernames(tweet: Dict[str, Any], author_id: Optional[str], in_reply_to_user_id: Optional[str]) -> Set[str]:
    """Build a set of lowercase usernames to exclude using includes.users id→username mapping."""
    excludes: Set[str] = set()
    includes_users: List[Dict[str, Any]] = ((tweet.get("includes") or {}).get("users") or [])  # type: ignore[assignment]
    id_to_username = {str(u.get("id")): (u.get("username") or "") for u in includes_users if u.get("id") and u.get("username")}
    if author_id and author_id in id_to_username:
        excludes.add(id_to_username[author_id].lower())
    if in_reply_to_user_id and in_reply_to_user_id in id_to_username:
        excludes.add(id_to_username[in_reply_to_user_id].lower())
    return excludes


def _id_to_username_map(tweet: Dict[str, Any]) -> Dict[str, str]:
    """Return id->username(lowercased) mapping from includes.users."""
    users = ((tweet.get("includes") or {}).get("users") or [])
    return {str(u.get("id")): (u.get("username") or "").lower()
            for u in users if u.get("id") and u.get("username")}


def extract_target_after_bot(
    tweet: Dict[str, Any],
    bot_handle_lc: str,
    author_id: Optional[str],
    in_reply_to_user_id: Optional[str],
) -> Optional[str]:
    """
    Returns the first explicit @mention (lowercased) that appears AFTER the bot's @mention in text.
    Excludes the bot handle, the tweet author, and the reply-context user (banner) by username mapping.
    """
    text = tweet.get("text", "") or ""
    mentions: List[Dict[str, Any]] = (tweet.get("entities") or {}).get("mentions") or []
    if not mentions or not text:
        return None

    # normalize and sort by text order
    for m in mentions:
        if isinstance(m.get("username"), str):
            m["username"] = m["username"]  # keep original case in dict; compare lower below
    mentions_sorted = [m for m in mentions if isinstance(m.get("start"), int)]
    mentions_sorted.sort(key=lambda m: m.get("start", 10**9))

    # Find first bot mention by position
    bot_positions = [m for m in mentions_sorted if (m.get("username") or "").lower() == bot_handle_lc]
    if not bot_positions:
        return None
    bot_start = min(m.get("start", -1) for m in bot_positions)
    if bot_start < 0:
        return None

    # Build exclusion set
    excluded_usernames: Set[str] = _build_excluded_usernames(tweet, author_id, in_reply_to_user_id)
    excluded_usernames.add(bot_handle_lc)

    # Scan trailing mentions in text order, pick first not excluded
    for m in mentions_sorted:
        s = m.get("start", 10**9)
        uname = (m.get("username") or "").lower()
        if s is None or not isinstance(s, int):
            continue
        if s <= bot_start:
            continue
        if not uname or uname in excluded_usernames:
            continue
        return uname

    return None


def typed_mentions(tweet: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Return (lowercased_text, typed_mentions) where typed_mentions are ONLY those
    whose entity offsets exactly equal '@{username}' slice in the current tweet text.
    This prevents 'merged' or 'ghost' mentions coming from referenced/parent tweets.
    """
    text: str = (tweet.get("text") or "")
    tlc = text.lower()
    ents: List[Dict[str, Any]] = (tweet.get("entities") or {}).get("mentions") or []

    typed: List[Dict[str, Any]] = []
    for m in ents:
        s, e = m.get("start"), m.get("end")
        uname = (m.get("username") or "").lower()
        if isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= len(text) and uname:
            # Accept ONLY if the actual slice equals '@{username}'
            if tlc[s:e] == f"@{uname}":
                typed.append({"start": s, "end": e, "username": uname, "id": m.get("id")})

    typed.sort(key=lambda m: m["start"])
    return tlc, typed


def _exclusions(tweet: Dict[str, Any], bot_handle_lc: str, author_id: Optional[str]) -> Set[str]:
    excludes: Set[str] = {bot_handle_lc}
    includes = ((tweet.get("includes") or {}).get("users") or [])
    id2u = {str(u.get("id")): (u.get("username") or "").lower() for u in includes if u.get("id") and u.get("username")}
    if author_id and author_id in id2u:
        excludes.add(id2u[author_id])
    return excludes


def extract_target_after_last_bot(
    tweet: Dict[str, Any],
    bot_handle_lc: str,
    author_id: Optional[str],
    in_reply_to_user_id: Optional[str],
) -> Tuple[Optional[str], str]:
    """
    Extract target after the last @bot mention with conversation-aware logic.
    
    Args:
        tweet: Tweet data
        bot_handle_lc: Bot handle in lowercase
        author_id: Tweet author ID
        in_reply_to_user_id: ID of user being replied to
        
    Returns:
        Tuple of (target_username, reason) or (None, reason)
    """
    tlc, typed = typed_mentions(tweet)
    if not tlc or not typed:
        return None, "no-mentions-or-text"

    # Find the last typed @bot anywhere in the text
    bot_idxs = [i for i, m in enumerate(typed) if m["username"] == bot_handle_lc]
    if not bot_idxs:
        return None, "bot-not-in-text"
    i = bot_idxs[-1]

    # Need an immediate next typed mention
    if i + 1 >= len(typed):
        return None, "no-next-mention"
    nxt = typed[i + 1]
    
    # Check gap between @bot and next mention
    text = tweet.get("text", "")
    gap = text[typed[i]["end"]:nxt["start"]]

    # Allow whitespace or optional single '+' between @bot and target
    if not re.fullmatch(r"[ \t\r\n]*\+?[ \t\r\n]*", gap or ""):
        return None, "gap-not-allowed"

    # Build exclusions (bot, author, reply-to user)
    excludes = _exclusions(tweet, bot_handle_lc, author_id)
    if in_reply_to_user_id:
        # Add reply-to user to exclusions
        includes_users = tweet.get("includes", {}).get("users", [])
        id_to_username = {str(u.get("id")): (u.get("username") or "").lower() 
                         for u in includes_users if u.get("id") and u.get("username")}
        if in_reply_to_user_id in id_to_username:
            excludes.add(id_to_username[in_reply_to_user_id])

    target = nxt["username"]
    if not target:
        return None, "empty-target"
    if target in excludes:
        return None, "excluded-target"

    # Light dedupe info for telemetry
    dedup = (i + 2 < len(typed) and typed[i + 2]["username"] == target)
    reason = "immediate after last @bot"
    if dedup:
        reason += " (dedup)"
    return target, reason

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
        return f"Welcome to $CRYBB @{target_username} 🍼\n\nNO CRYING IN THE CASINO."
    else:
        return "Welcome to $CRYBB 🍼\n\nNO CRYING IN THE CASINO."

def format_rate_limit_message() -> str:
    """Format a friendly rate limit message."""
    return "Hey! I'm getting a bit overwhelmed 😅 Please wait a bit before requesting another CryBB PFP!"

def format_error_message() -> str:
    """Format a friendly error message."""
    return "Oops! Something went wrong while processing your request. Please try again later! 🙏"




def is_reply_to_bot(tweet: Dict[str, Any], bot_id: str) -> bool:
    """
    Check if the tweet is a reply to the bot.
    
    Args:
        tweet: Tweet data
        bot_id: Bot's user ID
        
    Returns:
        True if replying to bot, False otherwise
    """
    in_reply_to_user_id = tweet.get("in_reply_to_user_id")
    return str(in_reply_to_user_id) == str(bot_id)


def get_parent_author_id(tweet: Dict[str, Any]) -> Optional[str]:
    """
    Get the author ID of the parent tweet from referenced_tweets.
    
    Args:
        tweet: Tweet data with referenced_tweets
        
    Returns:
        Parent author ID if found, None otherwise
    """
    referenced_tweets = tweet.get("referenced_tweets", [])
    for ref_tweet in referenced_tweets:
        if ref_tweet.get("type") == "replied_to":
            return ref_tweet.get("author_id")
    return None
