"""
Main processing loop for CryBB Maker Bot.
Handles mention polling, processing, and replying with intelligent rate limiting.
"""
import time
import threading
import sys
import os
from typing import Optional
from src.config import Config
from src.twitter_factory import make_twitter_client
from src.image_processor import ImageProcessor
from src.rate_limiter import RateLimiter
from src.per_user_limiter import PerUserLimiter, normalize
from src.storage import Storage
from src.utils import (
    extract_target_after_bot,
    extract_target_after_last_bot,
    typed_mentions,
    is_reply_to_bot,
    get_parent_author_id,
    normalize_pfp_url,
    format_friendly_message,
    format_rate_limit_message,
    format_error_message
)
from src.pipeline.orchestrator import Orchestrator
from src.batch_context import ProcessingContext

class CryBBBot:
    """Main bot class."""
    
    def __init__(self):
        """Initialize the bot."""
        print("Creating Twitter client...")
        self.twitter_client = make_twitter_client()
        print("✓ Twitter client created")
        
        print("Creating image processor...")
        self.image_processor = ImageProcessor()
        print("✓ Image processor created")
        
        print("Creating orchestrator...")
        self.orchestrator = Orchestrator(Config)
        print("✓ Orchestrator created")
        
        print("Creating rate limiter...")
        self.rate_limiter = RateLimiter()
        print("✓ Rate limiter created")
        
        print("Creating storage...")
        self.storage = Storage()
        print("✓ Storage created")
        
        # Clean up any stale processing locks from previous runs
        print("Cleaning up stale processing locks...")
        self.storage.cleanup_stale_processing_locks()
        print("✓ Stale processing locks cleaned up")
        
        print("Creating user limiter...")
        self.user_limiter = PerUserLimiter(Config.PER_TARGET_HOURLY_LIMIT, 3600)
        print("✓ User limiter created")
        
        self.sleeper_mode = False
        self.last_retweeted_id = None
        
        # Get bot identity
        print("Getting bot identity...")
        self.bot_id, self.bot_handle = self.twitter_client.get_bot_identity()
        print(f"✓ Bot initialized: @{self.bot_handle} (ID: {self.bot_id})")
    
    def resolve_target_user(self, target_username: str, ctx: ProcessingContext) -> dict | None:
        """Resolve target user with batch-first resolution strategy."""
        username_lc = (target_username or "").lower()

        # 1) Batch snapshot (preferred)
        u = ctx.get_user(username_lc)
        if u:
            return u

        # 2) Global cache fallback
        try:
            cached_user = self.twitter_client.get_user_by_username(target_username)
            if cached_user:
                user_data = {
                    "id": cached_user.id,
                    "username": cached_user.username,
                    "name": cached_user.name,
                    "profile_image_url": cached_user.profile_image_url,
                    "verified": cached_user.verified
                }
                # Pin for long jobs
                ctx.pin_user(username_lc, user_data)
                return user_data
        except Exception as e:
            print(f"Cache lookup failed for @{target_username}: {e}")

        # 3) Network fallback (rare): only if truly missing
        try:
            user = self.twitter_client.get_user_by_username(target_username)
            if user:
                user_data = {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "profile_image_url": user.profile_image_url,
                    "verified": user.verified
                }
                ctx.pin_user(username_lc, user_data)
                return user_data
        except Exception as e:
            print(f"Network lookup failed for @{target_username}: {e}")

        return None
    
    def process_mention(self, tweet_data: dict, ctx: ProcessingContext) -> None:
        """
        Process a single mention using conversation-aware logic.
        """
        try:
            # Extract basic info from tweet data
            author_id = str(tweet_data.get('author_id', ''))
            tweet_text = tweet_data.get('text', '')
            tweet_id = tweet_data.get('id', '')
            conversation_id = tweet_data.get('conversation_id')
            in_reply_to_user_id = tweet_data.get('in_reply_to_user_id')
            
            # Determine reply target: use conversation_id (root tweet) if available, otherwise tweet_id
            reply_to_id = conversation_id if conversation_id else tweet_id
            
            # CRITICAL FIX: Enhanced debug logging to show what we're actually processing
            author_username = (tweet_data.get('author') or {}).get('username') or 'unknown'
            print(f"[MENTION PROCESSING] Processing tweet_id={tweet_id} author=@{author_username} text=\"{tweet_text}\"")
            
            # HARD GUARD: Only proceed if @bot appears in the actual text of this tweet.
            bot_handle_lc = (self.bot_handle or Config.BOT_HANDLE).lstrip("@").lower()
            txt_lc = (tweet_text or "").lower()
            
            if f"@{bot_handle_lc}" not in txt_lc:
                print("[SKIP] No explicit @bot in tweet text; ignoring")
                return
            
            # OPTIONAL: surface how many typed mentions we have for debugging
            tlc, typed = typed_mentions(tweet_data)
            if not typed:
                print("[SKIP] No typed mentions in current tweet text; ignoring")
                return
            
            print(f"[VALIDATION PASSED] Tweet {tweet_id} contains @bot mention in its own text")
            
            # Check if this is a reply to bot
            reply_to_bot = is_reply_to_bot(tweet_data, self.bot_id)
            
            # Get parent author ID for logging
            parent_author_id = get_parent_author_id(tweet_data)
            
            # Conversation-aware logic
            if reply_to_bot:
                # Reply to bot: require strict explicit pair
                # @bot must be FIRST typed mention and immediately followed by @target
                if len(typed) < 2 or typed[0]["username"] != bot_handle_lc:
                    print("[SKIP] Reply to bot without explicit @bot @target pair")
                    return
                
                # Check if @bot is immediately followed by another mention
                if typed[1]["start"] != typed[0]["end"] + 1:  # Allow single space
                    gap = tweet_text[typed[0]["end"]:typed[1]["start"]]
                    if gap.strip() and gap.strip() != "+":
                        print("[SKIP] Reply to bot without immediate @target after @bot")
                        return
                
                target_username, reason = extract_target_after_last_bot(
                    tweet_data, bot_handle_lc, author_id, in_reply_to_user_id, len(typed)
                )
            else:
                # Not replying to bot: determine behavior based on mention count
                if len(typed) >= 3:
                    # For 3+ mentions: allow @bot + @user pattern ANYWHERE in the tweet
                    bot_positions = [i for i, m in enumerate(typed) if m["username"] == bot_handle_lc]
                    if not bot_positions:
                        print("[SKIP] @bot not found in tweet with 3+ mentions")
                        return

                    pattern_found = False
                    # Check for @bot + @user pattern anywhere
                    for bot_idx in bot_positions:
                        if bot_idx + 1 < len(typed):
                            gap = tweet_text[typed[bot_idx]["end"]:typed[bot_idx + 1]["start"]]
                            if gap.strip() == "+" and typed[bot_idx + 1]["username"] != bot_handle_lc:
                                # Found @bot + @user pattern
                                pattern_found = True
                                print(f"[PATTERN MATCHED] @bot + @user (3+ mentions, position {bot_idx})")
                                break
                    
                    if not pattern_found:
                        print("[SKIP] No @bot + @user pattern found in tweet with 3+ mentions")
                        return

                else:
                    # For <3 mentions: require @bot as FIRST mention, + symbol is OPTIONAL
                    if not typed or typed[0]["username"] != bot_handle_lc:
                        print("[SKIP] @bot not first typed mention in tweet with <3 mentions")
                        return

                    # Check for @bot + @user pattern (must be first), + is optional
                    if len(typed) >= 2:
                        gap = tweet_text[typed[0]["end"]:typed[1]["start"]]
                        if gap.strip() == "+":
                            print("[PATTERN MATCHED] @bot + @user (<3 mentions, @bot first, with +)")
                        else:
                            print("[PATTERN MATCHED] @bot @user (<3 mentions, @bot first, no + needed)")
                    else:
                        print("[PATTERN MATCHED] @bot only mention")
                
                if Config.DEBUG_MODE:
                    print(f"[MENTION DEBUG] Checking pattern: {tweet_text}")
                target_username, reason = extract_target_after_last_bot(
                    tweet_data, bot_handle_lc, author_id, in_reply_to_user_id, len(typed)
                )
            
            # Enhanced debug logging with tweet validation
            author_username = (tweet_data.get('author') or {}).get('username') or ''
            if Config.DEBUG_MODE:
                print(f"[MENTION DEBUG] id={tweet_id} conv={conversation_id} reply_to={in_reply_to_user_id} "
                      f"author=@{author_username} target=@{target_username or 'None'} reason=\"{reason}\" "
                      f"text=\"{tweet_text}\" parent_author={parent_author_id}")
            
            # CRITICAL FIX: Final validation - ensure tweet text matches what we're processing
            # This prevents processing wrong tweets in conversation threads
            if tweet_text and not any(bot_handle_lc in tweet_text.lower() for bot_handle_lc in [self.bot_handle.lstrip("@").lower(), Config.BOT_HANDLE.lstrip("@").lower()]):
                print(f"[CRITICAL ERROR] Tweet {tweet_id} text does not contain @bot mention!")
                print(f"[CRITICAL ERROR] Tweet text: \"{tweet_text}\"")
                print(f"[CRITICAL ERROR] Expected bot handles: @{self.bot_handle}, @{Config.BOT_HANDLE}")
                return
            
            if not target_username:
                print(f"[SKIP] {reason}")
                return

            # Get author username from batch snapshot for rate limiting
            author_username = None
            if 'author' in tweet_data:
                # Use expanded author data from mentions response (no extra API call needed!)
                author_data = tweet_data['author']
                author_username = author_data.get('username')
            
            # Check rate limit
            if not self.rate_limiter.allow(author_id, author_username):
                print(f"Rate limit exceeded for user {author_username or author_id}")
                self.twitter_client.reply_with_image(
                    reply_to_id,
                    format_rate_limit_message(),
                    self._create_error_image()
                )
                return
            else:
                if author_username:
                    print(f"Incoming limiter OK for @{author_username}")
            
            # Get whitelist status for rate-limit bypass
            from src.per_user_limiter import normalize
            normalized_username = normalize(author_username) if author_username else ""
            is_whitelisted = normalized_username in Config.WHITELIST_HANDLES
            
            if Config.DEBUG_MODE:
                print(f"[DEBUG] Processing mention from user @{author_username}")
            
            # Additional validation
            from src.per_user_limiter import normalize
            if normalize(target_username) == normalize(Config.BOT_HANDLE):
                print("[SKIP] Target is bot handle")
                return
            
            # Conversation de-dupe check
            if conversation_id and self.storage.check_conversation_dedupe(conversation_id, target_username):
                print(f"[SKIP] conv-dedupe: already processed {conversation_id} -> @{target_username} recently")
                return
            # Per-target limiter (no whitelist bypass - all users treated equally)
            if not self.user_limiter.allow(target_username):
                print(f"Per-target limit reached for @{target_username}; skipping.")
                return
            else:
                print(f"Per-target count @{target_username} = {self.user_limiter.count(target_username)} in last hour")
            
            # Get target user and profile image using batch-first resolution
            target_user_data = self.resolve_target_user(target_username, ctx)
            
            if not target_user_data:
                print(f"Could not fetch user @{target_username}")
                self.twitter_client.reply_with_image(
                    reply_to_id,
                    format_error_message(),
                    self._create_error_image()
                )
                return
            
            # Block self-PFP explicitly
            if normalize(target_username) == normalize(Config.BOT_HANDLE):
                print("[SKIP] Self-PFP attempt for bot handle; ignoring")
                return

            pfp_url = normalize_pfp_url(target_user_data.get('profile_image_url') or "")
            print(f"PFP={pfp_url}")
            
            if not pfp_url:
                print(f"No profile image URL for @{target_username}")
                self.twitter_client.reply_with_image(
                    reply_to_id,
                    format_error_message(),
                    self._create_error_image()
                )
                return
            
            # Pin user data for long-running AI processing
            if target_user_data:
                ctx.pin_user(target_user_data["username"].lower(), target_user_data)
            
            # Generate image with [style, target_pfp] order
            image_bytes = self.orchestrator.render_with_urls(
                [Config.CRYBB_STYLE_URL, pfp_url],
                mention_text=tweet_text or ""
            )
            
            # Reply with processed image
            reply_text = format_friendly_message(target_username)
            
            # Enhanced logging to show reply target decision
            if conversation_id and conversation_id != tweet_id:
                print(f"[REPLY STRATEGY] Using conversation_id {conversation_id} (root tweet) instead of tweet_id {tweet_id} (intermediate reply)")
                print(f"[REPLY STRATEGY] This ensures the reply appears directly under the original tweet")
            else:
                print(f"[REPLY STRATEGY] Using tweet_id {tweet_id} (no conversation or same as root)")

            reply_result = self.twitter_client.reply_with_image(reply_to_id, reply_text, image_bytes)
            
            # Record conversation de-dupe after successful reply
            if conversation_id:
                self.storage.record_conversation_dedupe(conversation_id, target_username)
            
            # Optional success log
            try:
                if reply_result and isinstance(reply_result, dict):
                    new_tweet_id = reply_result.get('id') or reply_result.get('data', {}).get('id')
                else:
                    new_tweet_id = None
                print(f"[REPLY OK] parent_id={tweet_id} reply_id={new_tweet_id or 'unknown'} target=@{target_username}")
            except Exception:
                pass
            
            # Update metrics
            from src.server import update_metrics
            update_metrics(processed=1, replies_sent=1, last_mention_time=tweet_data.get('created_at'))
            
        except Exception as e:
            print(f"Error processing mention {tweet_data.get('id', 'unknown')}: {e}")
            try:
                # Use conversation_id if available, otherwise tweet_id
                error_reply_to_id = tweet_data.get('conversation_id') or tweet_data.get('id', '')
                self.twitter_client.reply_with_image(
                    error_reply_to_id,
                    format_error_message(),
                    self._create_error_image()
                )
                # Update error metrics
                from src.server import update_metrics
                update_metrics(processed=1, ai_fail=1)
            except:
                print("Failed to send error reply")
                # Update error metrics
                from src.server import update_metrics
                update_metrics(processed=1, ai_fail=1)
    
    def _create_error_image(self) -> bytes:
        """Create a simple error image."""
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Create a simple error image
        img = Image.new('RGB', (400, 400), color='red')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 200), "Error processing image", font=font, fill='white')
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=90)
        return output.getvalue()
    
    def run_polling_loop(self) -> None:
        """
        Run the main polling loop with adaptive rate limiting.
        Dynamically adjusts polling frequency based on rate limit status.
        """
        since_id = self.storage.read_since_id()
        backoff_seconds = 1
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                print(f"Polling for mentions since ID: {since_id}")
                
                # Check rate limit status before making requests
                rate_status = self.twitter_client.get_rate_limit_status()
                print(f"Rate limit status: {rate_status}")
                
                # Fetch mentions
                mentions_response = self.twitter_client.get_mentions(since_id)

                # If rate-limited marker, skip processing and sleeping handled by client
                if isinstance(mentions_response, dict) and mentions_response.get("rate_limited"):
                    # Do not change mode, just continue loop
                    continue
                
                # Extract mentions and includes from response
                mentions = mentions_response.get("tweets", []) if isinstance(mentions_response, dict) else mentions_response
                includes = mentions_response.get("includes", {}) if isinstance(mentions_response, dict) else {}
                users = includes.get("users", []) or []
                
                if mentions:
                    if Config.DEBUG_MODE:
                        print(f"Found {len(mentions)} mentions")
                    
                    # Build batch snapshot from includes.users
                    from src.x_v2 import _normalize_user_min
                    batch_users = {
                        (u.get("username", "").lower()): _normalize_user_min(u)
                        for u in users if u.get("username")
                    }
                    
                    ctx = ProcessingContext(batch_users=batch_users)
                    if Config.DEBUG_MODE:
                        print(f"Built batch snapshot: users={len(batch_users)}")
                    
                    # Process mentions with contiguous success tracking
                    processed_ids = self.storage.read_processed_ids()
                    oldest_first = mentions  # assumed oldest→newest
                    success_ids: set[str] = set()
                    failed_ids: list[str] = []
                    
                    def highest_processed_id(seq):
                        """
                        Return the highest tweet_id that was processed (successfully or not) in the batch.
                        This allows since_id to advance past failed tweets to continue processing newer ones.
                        """
                        highest = None
                        processed_ids = set()
                        
                        # Include already processed tweets
                        for m in seq:
                            tid = m["id"]
                            if self.storage.is_processed(tid):
                                processed_ids.add(tid)
                                if highest is None or tid > highest:
                                    highest = tid
                        
                        # Include tweets processed in this batch (success or failure)
                        for tid in success_ids:
                            processed_ids.add(tid)
                            if highest is None or tid > highest:
                                highest = tid
                        
                        for tid in failed_ids:
                            processed_ids.add(tid)
                            if highest is None or tid > highest:
                                highest = tid
                        
                        return highest
                    
                    # Count already-processed as success so they contribute to the prefix.
                    for m in oldest_first:
                        tid = m["id"]
                        if self.storage.is_processed(tid):
                            success_ids.add(tid)
                    
                    # Log every mention retrieved from Twitter API
                    if Config.DEBUG_MODE:
                        print(f"[BATCH DEBUG] Retrieved {len(oldest_first)} mentions from Twitter API")
                        for i, m in enumerate(oldest_first):
                            tid = m["id"]
                            author_username = (m.get('author') or {}).get('username') or 'unknown'
                            tweet_text = m.get('text', '')
                            is_already_processed = tid in success_ids
                            print(f"[MENTION {i+1}/{len(oldest_first)}] ID={tid} author=@{author_username} text=\"{tweet_text[:50]}...\" processed={is_already_processed}")
                    
                    for m in oldest_first:
                        tid = m["id"]
                        if tid in success_ids:
                            # Already processed earlier (or in previous runs)
                            print(f"[SKIP] Tweet {tid} already processed in previous run")
                            continue
                        
                        # Check if tweet is currently being processed by another instance
                        if self.storage.is_processing(tid):
                            print(f"[SKIP] Tweet {tid} is currently being processed by another instance")
                            continue
                        
                        # Acquire processing lock to prevent concurrent processing
                        if not self.storage.acquire_processing_lock(tid):
                            print(f"[SKIP] Tweet {tid} processing lock could not be acquired")
                            continue
                        
                        try:
                            # ---- your existing routing (AI vs overlay vs text rules) is inside process_mention() ----
                            print(f"[PROCESSING] Starting processing for tweet {tid}")
                            self.process_mention(m, ctx)
                            
                            # Only mark as processed if processing was successful
                            if self.storage.mark_processed(tid):
                                success_ids.add(tid)
                                print(f"✅ Processed {tid}")
                            else:
                                print(f"⚠️ Tweet {tid} was already processed by another instance")
                                
                        except Exception as e:
                            print(f"❌ Failed {tid}: {e}")
                            # Try a text-only fallback reply ONCE.
                            try:
                                self.twitter_client.create_reply_text(
                                    in_reply_to=tid,
                                    text="Sorry — I couldn't render that one. Try again in a bit! 💛"
                                )
                                if self.storage.mark_processed(tid):
                                    success_ids.add(tid)
                                    print(f"📝 Sent fallback text for {tid}")
                                else:
                                    print(f"⚠️ Tweet {tid} was already processed by another instance")
                            except Exception as e2:
                                print(f"⚠️ Fallback also failed for {tid}: {e2}")
                                failed_ids.append(tid)
                                # Mark as processed to prevent infinite retry loops
                                # since_id will still advance past this tweet
                                if self.storage.mark_processed(tid):
                                    print(f"📝 Marked failed tweet {tid} as processed to prevent retry loops")
                                else:
                                    print(f"⚠️ Failed tweet {tid} was already processed by another instance")
                        finally:
                            # Always release the processing lock
                            self.storage.release_processing_lock(tid)
                    
                    # Advance since_id to the highest tweet ID processed (successfully or not).
                    # This allows the bot to continue processing newer tweets even if some older ones fail.
                    highest_processed = highest_processed_id(oldest_first)
                    if highest_processed:
                        prev = self.storage.read_since_id()
                        if highest_processed != prev:
                            self.storage.write_since_id(highest_processed)
                            print(f"📝 since_id → {highest_processed} (advanced past {len(failed_ids)} failed tweets)")
                        else:
                            print(f"📝 since_id unchanged at {highest_processed} (no new tweets processed)")
                    else:
                        print(f"📝 since_id unchanged (no tweets processed in this batch)")
                    
                    if failed_ids:
                        print(f"⏳ Will retry next poll: {failed_ids}")
                    
                    # Debug log
                    print(f"📦 Batch done: successes={len(success_ids)} failures={len(failed_ids)} since_id={self.storage.read_since_id()}")
                    
                    # Reset backoff and error counters on successful processing
                    backoff_seconds = 1
                    consecutive_errors = 0
                else:
                    print("No new mentions found")
                
                # Mode & sleeper tracking
                self.sleeper_mode = (len(mentions) == 0)
                print(f"Mode set to {'sleeper' if self.sleeper_mode else 'awake'}; mentions_count={len(mentions)}")

                # Sleeper-mode retweet if quiet
                if self.sleeper_mode:
                    try:
                        bot_id, bot_handle = self.twitter_client.get_bot_identity()
                        tweets = self.twitter_client.get_user_tweets(bot_id, max_results=20)
                        if isinstance(tweets, dict) and tweets.get("rate_limited"):
                            # Skip RT this cycle if timeline is rate-limited
                            pass
                        else:
                            tweets_list = tweets if isinstance(tweets, list) else (tweets or [])
                            candidate = None
                            likes_for_log = 0
                            for t in tweets_list:
                                metrics = t.get('public_metrics') or {}
                                likes = metrics.get('like_count', 0)
                                if likes >= Config.RT_LIKE_THRESHOLD:
                                    if t.get('id') != self.last_retweeted_id:
                                        candidate = t
                                        likes_for_log = likes
                                        break
                            if candidate:
                                try:
                                    r = self.twitter_client.retweet_v11(candidate['id'])
                                    if isinstance(r, dict) and r.get("rate_limited"):
                                        # Skip if retweet route is rate-limited
                                        pass
                                    else:
                                        self.last_retweeted_id = candidate['id']
                                        print(f"Retweeted sleeper candidate {candidate['id']} (likes={likes_for_log}).")
                                except Exception as e:
                                    print(f"Retweet failed for {candidate['id']}: {e}")
                            else:
                                print("No sleeper RT candidate (>= like threshold) found.")
                    except Exception as e:
                        print(f"Sleeper RT logic error: {e}")

                # Adaptive polling with jitter (non-429 path)
                import random
                # If mentions route remaining <= 1, sleep until reset+5s
                rl = self.twitter_client.get_rate_limit_status() or {}
                mentions_rl = rl.get('users/mentions')
                if mentions_rl and isinstance(mentions_rl.get('remaining'), int) and mentions_rl.get('remaining') <= 1:
                    now = time.time()
                    reset_ts = mentions_rl.get('reset', int(now))
                    wait = max(0, reset_ts - int(now)) + 5
                else:
                    if self.sleeper_mode:
                        wait = random.randint(480, 600)
                    else:
                        wait = random.randint(Config.AWAKE_MIN_SECS, Config.AWAKE_MAX_SECS)
                print(f"Next poll in {wait}s (mode={'sleeper' if self.sleeper_mode else 'awake'}).")
                time.sleep(wait)
                
            except Exception as e:
                consecutive_errors += 1
                print(f"Error in polling loop (attempt {consecutive_errors}): {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    print(f"Too many consecutive errors ({consecutive_errors}). Backing off significantly.")
                    time.sleep(300)  # Wait 5 minutes
                    consecutive_errors = 0
                else:
                    # Exponential backoff with cap
                    backoff_seconds = min(backoff_seconds * 2, 300)  # Cap at 5 minutes
                    print(f"Backing off for {backoff_seconds} seconds")
                    time.sleep(backoff_seconds)
    
    
    def start(self) -> None:
        """Start the bot."""
        print("Starting CryBB Maker Bot...")
        
        # Start health server in background thread
        def run_health_server():
            import uvicorn
            from src.server import app
            uvicorn.run(app, host="0.0.0.0", port=Config.PORT, log_level="warning")
        
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        print(f"Health server started on port {Config.PORT}")
        
        # Start polling loop
        self.run_polling_loop()

def main():
    """Main entry point."""
    try:
        print("=== CryBB Bot Starting ===")
        print(f"Python version: {sys.version}")
        print(f"Working directory: {os.getcwd()}")
        print(f"Python path: {sys.path}")
        
        # Validate configuration before proceeding
        print("Validating configuration...")
        Config.validate()
        print("✓ Configuration validation passed")
        
        print("Initializing bot...")
        bot = CryBBBot()
        print("✓ Bot initialization completed")
        
        print("Starting bot...")
        bot.start()
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
