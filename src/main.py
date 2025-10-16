"""
Main processing loop for CryBB Maker Bot.
Handles mention polling, processing, and replying with intelligent rate limiting.
"""
import time
import threading
from typing import Optional
from src.config import Config
from src.twitter_factory import make_twitter_client
from src.image_processor import ImageProcessor
from src.rate_limiter import RateLimiter
from src.per_user_limiter import PerUserLimiter, normalize
from src.storage import Storage
from src.utils import (
    extract_target_after_bot,
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
        self.twitter_client = make_twitter_client()
        self.image_processor = ImageProcessor()
        self.orchestrator = Orchestrator(Config)
        self.rate_limiter = RateLimiter()
        self.storage = Storage()
        self.user_limiter = PerUserLimiter(Config.PER_TARGET_HOURLY_LIMIT, 3600)
        self.sleeper_mode = False
        self.last_retweeted_id = None
        
        # Get bot identity
        self.bot_id, self.bot_handle = self.twitter_client.get_bot_identity()
        print(f"Bot initialized: @{self.bot_handle} (ID: {self.bot_id})")
    
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
        Process a single mention using the new v2 client interface.
        Optimized to minimize API calls through intelligent caching.
        """
        try:
            # Extract author info from tweet data
            author_id = str(tweet_data.get('author_id', ''))
            tweet_text = tweet_data.get('text', '')
            tweet_id = tweet_data.get('id', '')
            
            print(f"Processing mention from {author_id}: {tweet_text}")
            
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
                    tweet_id,
                    format_rate_limit_message(),
                    self._create_error_image()
                )
                return
            else:
                if author_username:
                    print(f"Incoming limiter OK for @{author_username}")
            
            # Get full author info - use cached data if available from mentions expansion
            author_verified = False
            if 'author' in tweet_data:
                # Use expanded author data from mentions response (no extra API call needed!)
                author_data = tweet_data['author']
                author_verified = author_data.get('verified', False)
                verified_type = author_data.get('verified_type')  # e.g., 'blue', 'business', 'government'
                effective_verified = author_verified or (verified_type in {"blue", "business", "government"})

                from src.per_user_limiter import normalize
                normalized_username = normalize(author_username) if author_username else ""
                is_whitelisted = normalized_username in Config.WHITELIST_HANDLES

                print(f"[DEBUG] User: @{author_username}, Verified={author_verified}, "
                      f"VerifiedType={verified_type}, EffectiveVerified={effective_verified}, "
                      f"InWhitelist={is_whitelisted}, Whitelist={list(Config.WHITELIST_HANDLES)}")

                # Accept if verified (any type) or whitelisted
                if not effective_verified and not is_whitelisted:
                    print(f"[DEBUG] Skipping mention from non-verified, non-whitelisted user @{author_username}")
                    return
                else:
                    if effective_verified:
                        print(f"[DEBUG] Processing mention from verified user @{author_username}")
                    else:
                        print(f"[DEBUG] Processing mention from whitelisted user @{author_username}")
            else:
                # Fallback: get author info via API call (should rarely happen with proper expansions)
                author = self.twitter_client.get_user_by_id(author_id)
                author_username = author.username if author else None
                author_verified = (author.verified if author else False)
                verified_type = getattr(author, 'verified_type', None)
                effective_verified = author_verified or (verified_type in {"blue", "business", "government"})

                from src.per_user_limiter import normalize
                normalized_username = normalize(author_username) if author_username else ""
                is_whitelisted = normalized_username in Config.WHITELIST_HANDLES
                print(f"Fetched author data via API: @{author_username} (verified: {author_verified}, verified_type: {verified_type}, effective_verified: {effective_verified})")
                
                print(f"[DEBUG] User: @{author_username}, Verified={author_verified}, "
                      f"VerifiedType={verified_type}, EffectiveVerified={effective_verified}, "
                      f"InWhitelist={is_whitelisted}, Whitelist={list(Config.WHITELIST_HANDLES)}")
                
                # Accept if verified (any type) or whitelisted
                if not effective_verified and not is_whitelisted:
                    print(f"[DEBUG] Skipping mention from non-verified, non-whitelisted user @{author_username}")
                    return
                else:
                    if effective_verified:
                        print(f"[DEBUG] Processing mention from verified user @{author_username}")
                    else:
                        print(f"[DEBUG] Processing mention from whitelisted user @{author_username}")
            
            # Extract target using new robust method
            target_username = extract_target_after_bot(tweet_data, Config.BOT_HANDLE, author_username or "")
            
            print(f"Target chosen: @{target_username}")
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
                    tweet_id,
                    format_error_message(),
                    self._create_error_image()
                )
                return
            
            pfp_url = normalize_pfp_url(target_user_data.get('profile_image_url') or "")
            print(f"PFP={pfp_url}")
            
            if not pfp_url:
                print(f"No profile image URL for @{target_username}")
                self.twitter_client.reply_with_image(
                    tweet_id,
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
            reply_text = f"Here's your CryBB PFP @{target_username} 🍼"
            self.twitter_client.reply_with_image(tweet_id, reply_text, image_bytes)
            
            # Update metrics
            from src.server import update_metrics
            update_metrics(processed=1, replies_sent=1, last_mention_time=tweet_data.get('created_at'))
            
        except Exception as e:
            print(f"Error processing mention {tweet_data.get('id', 'unknown')}: {e}")
            try:
                self.twitter_client.reply_with_image(
                    tweet_data.get('id', ''),
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
                    print(f"Found {len(mentions)} mentions")
                    
                    # Build batch snapshot from includes.users
                    from src.x_v2 import _normalize_user_min
                    batch_users = {
                        (u.get("username", "").lower()): _normalize_user_min(u)
                        for u in users if u.get("username")
                    }
                    
                    ctx = ProcessingContext(batch_users=batch_users)
                    print(f"Built batch snapshot: users={len(batch_users)}")
                    
                    # Process mentions with contiguous success tracking
                    processed_ids = self.storage.read_processed_ids()
                    oldest_first = mentions  # assumed oldest→newest
                    success_ids: set[str] = set()
                    failed_ids: list[str] = []
                    
                    def last_contiguous_success(seq):
                        """
                        Return the last tweet_id of the contiguous success prefix from the oldest.
                        A 'success' means the tweet_id is in success_ids (including already processed).
                        """
                        last = None
                        for m in seq:
                            tid = m["id"]
                            if tid in success_ids:
                                last = tid
                            else:
                                break
                        return last
                    
                    # Count already-processed as success so they contribute to the prefix.
                    for m in oldest_first:
                        tid = m["id"]
                        if self.storage.is_processed(tid):
                            success_ids.add(tid)
                    
                    for m in oldest_first:
                        tid = m["id"]
                        if tid in success_ids:
                            # Already processed earlier (or in previous runs)
                            continue
                        
                        try:
                            # ---- your existing routing (AI vs overlay vs text rules) is inside process_mention() ----
                            self.process_mention(m, ctx)
                            self.storage.mark_processed(tid)
                            success_ids.add(tid)
                            print(f"✅ Processed {tid}")
                        except Exception as e:
                            print(f"❌ Failed {tid}: {e}")
                            # Try a text-only fallback reply ONCE.
                            try:
                                self.twitter_client.create_reply_text(
                                    in_reply_to=tid,
                                    text="Sorry — I couldn't render that one. Try again in a bit! 💛"
                                )
                                self.storage.mark_processed(tid)
                                success_ids.add(tid)
                                print(f"📝 Sent fallback text for {tid}")
                            except Exception as e2:
                                print(f"⚠️ Fallback also failed for {tid}: {e2}")
                                failed_ids.append(tid)
                                # leave unmarked so it retries next poll
                    
                    # Advance since_id only to last *contiguous* success from the oldest.
                    prefix_last = last_contiguous_success(oldest_first)
                    if prefix_last:
                        prev = self.storage.read_since_id()
                        if prefix_last != prev:
                            self.storage.write_since_id(prefix_last)
                            print(f"📝 since_id → {prefix_last}")
                    
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
        bot = CryBBBot()
        bot.start()
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
