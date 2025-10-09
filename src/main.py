"""
Main processing loop for CryBB Maker Bot.
Handles mention polling, processing, and replying with intelligent rate limiting.
"""
import time
import threading
from typing import Optional
from config import Config
from twitter_factory import make_twitter_client
from image_processor import ImageProcessor
from rate_limiter import RateLimiter
from storage import Storage
from utils import (
    extract_target_after_bot,
    normalize_pfp_url,
    format_friendly_message,
    format_rate_limit_message,
    format_error_message
)
from pipeline.orchestrator import Orchestrator

class CryBBBot:
    """Main bot class."""
    
    def __init__(self):
        """Initialize the bot."""
        self.twitter_client = make_twitter_client()
        self.image_processor = ImageProcessor()
        self.orchestrator = Orchestrator(Config)
        self.rate_limiter = RateLimiter()
        self.storage = Storage()
        
        # Get bot identity
        self.bot_id, self.bot_handle = self.twitter_client.get_bot_identity()
        print(f"Bot initialized: @{self.bot_handle} (ID: {self.bot_id})")
    
    def process_mention(self, tweet_data: dict) -> None:
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
            
            # Check rate limit
            if not self.rate_limiter.allow(author_id):
                print(f"Rate limit exceeded for user {author_id}")
                self.twitter_client.reply_with_image(
                    tweet_id,
                    format_rate_limit_message(),
                    self._create_error_image()
                )
                return
            
            # Get author info - use cached data if available from mentions expansion
            author_username = None
            if 'author' in tweet_data:
                # Use expanded author data from mentions response (no extra API call needed!)
                author_data = tweet_data['author']
                author_username = author_data.get('username')
                print(f"Using cached author data: @{author_username}")
            else:
                # Fallback: get author info via API call (should rarely happen with proper expansions)
                author = self.twitter_client.get_user_by_id(author_id)
                author_username = author.username if author else None
                print(f"Fetched author data via API: @{author_username}")
            
            # Extract target using new robust method
            target_username = extract_target_after_bot(tweet_data, Config.BOT_HANDLE, author_username or "")
            
            print(f"Target chosen: @{target_username}")
            
            # Get target user and profile image - try expanded data first
            target_user_data = None
            if 'mentioned_users' in tweet_data and target_username in tweet_data['mentioned_users']:
                # Use expanded user data (no API call needed!)
                target_user_data = tweet_data['mentioned_users'][target_username]
                print(f"Using cached target user data: @{target_username}")
            else:
                # Fallback: get target user via API call
                target_user = self.twitter_client.get_user_by_username(target_username)
                if target_user:
                    target_user_data = {
                        'id': target_user.id,
                        'username': target_user.username,
                        'name': target_user.name,
                        'profile_image_url': target_user.profile_image_url
                    }
                    print(f"Fetched target user data via API: @{target_username}")
            
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
            
            # Generate image with [style, target_pfp] order
            image_bytes = self.orchestrator.render_with_urls(
                [Config.CRYBB_STYLE_URL, pfp_url],
                mention_text=tweet_text or ""
            )
            
            # Reply with processed image
            reply_text = f"Here's your CryBB PFP @{target_username} 🍼"
            self.twitter_client.reply_with_image(tweet_id, reply_text, image_bytes)
            
            # Update metrics
            from server import update_metrics
            update_metrics(processed=1, replies_sent=1, last_mention_time=tweet_data.get('created_at'))
            
            print(f"Successfully processed mention {tweet_id}")
            
        except Exception as e:
            print(f"Error processing mention {tweet_data.get('id', 'unknown')}: {e}")
            try:
                self.twitter_client.reply_with_image(
                    tweet_data.get('id', ''),
                    format_error_message(),
                    self._create_error_image()
                )
                # Update error metrics
                from server import update_metrics
                update_metrics(processed=1, ai_fail=1)
            except:
                print("Failed to send error reply")
                # Update error metrics
                from server import update_metrics
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
                mentions = self.twitter_client.get_mentions(since_id)
                
                if mentions:
                    print(f"Found {len(mentions)} mentions")
                    
                    # Process mentions (oldest first)
                    for mention in mentions:
                        self.process_mention(mention)
                        since_id = mention['id']  # Updated for dict interface
                    
                    # Save since_id
                    self.storage.write_since_id(since_id)
                    
                    # Reset backoff and error counters on successful processing
                    backoff_seconds = 1
                    consecutive_errors = 0
                else:
                    print("No new mentions found")
                
                # Smart polling based on activity
                if mentions:
                    wait_time = 5 * 60   # 5 minutes when active
                else:
                    wait_time = 30 * 60  # 30 minutes when quiet
                print(f"Waiting {wait_time} seconds before next poll")
                time.sleep(wait_time)
                
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
            from server import app
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
