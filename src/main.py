"""
Main processing loop for CryBB Maker Bot.
Handles mention polling, processing, and replying.
"""
import time
import threading
import tweepy
from typing import Optional
from .config import Config
from .twitter_factory import make_twitter_client
from .image_processor import ImageProcessor
from .rate_limiter import RateLimiter
from .storage import Storage
from .utils import (
    extract_target_username,
    format_friendly_message,
    format_rate_limit_message,
    format_error_message
)
from .pipeline.orchestrator import Orchestrator

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
    
    def process_mention(self, tweet) -> None:
        """Process a single mention."""
        try:
            # Extract author info
            author_id = str(tweet.author_id)
            tweet_text = tweet.text
            tweet_id = tweet.id
            
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
            
            # Extract target username
            target_username = extract_target_username(tweet_text, self.bot_handle)
            if not target_username:
                # Fallback to author's username via client
                try:
                    user = self.twitter_client.get_user_by_id(int(author_id))
                    if user and user.get("username"):
                        target_username = user["username"]
                except Exception:
                    target_username = None
            
            # Get profile image URL
            if target_username:
                user = self.twitter_client.get_user_by_username(target_username)
                profile_url = user.get("profile_image_url") if user else None
            else:
                profile_url = None
            
            if not profile_url:
                print(f"Could not fetch profile image for @{target_username}")
                self.twitter_client.reply_with_image(
                    tweet_id,
                    format_error_message(),
                    self._create_error_image()
                )
                return
            
            # Download profile image
            image_bytes = self.twitter_client.download_bytes(profile_url)
            if not image_bytes:
                print(f"Could not download image from {profile_url}")
                self.twitter_client.reply_with_image(
                    tweet_id,
                    format_error_message(),
                    self._create_error_image()
                )
                return
            
            # Generate image via AI orchestrator (fallbacks to placeholder)
            processed_image = self.orchestrator.render(
                pfp_url=profile_url,
                mention_text=tweet_text or "",
            )
            
            # Reply with processed image
            reply_text = format_friendly_message(target_username)
            self.twitter_client.reply_with_image(tweet_id, reply_text, processed_image)
            
            print(f"Successfully processed mention {tweet_id}")
            
        except Exception as e:
            print(f"Error processing mention {tweet.id}: {e}")
            try:
                self.twitter_client.reply_with_image(
                    tweet.id,
                    format_error_message(),
                    self._create_error_image()
                )
            except:
                print("Failed to send error reply")
    
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
        """Run the main polling loop."""
        since_id = self.storage.read_since_id()
        
        while True:
            try:
                print(f"Polling for mentions since ID: {since_id}")
                
                # Fetch mentions
                mentions = self.twitter_client.get_mentions(since_id)
                
                if mentions:
                    print(f"Found {len(mentions)} mentions")
                    
                    # Process mentions (oldest first)
                    for mention in mentions:
                        self.process_mention(mention)
                        since_id = mention.id
                    
                    # Save since_id
                    self.storage.write_since_id(since_id)
                else:
                    print("No new mentions found")
                
                # Wait before next poll
                time.sleep(Config.POLL_SECONDS)
                
            except tweepy.TooManyRequests as e:
                print(f"Rate limited: {e}")
                # Wait longer on rate limit
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                print(f"Error in polling loop: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def start(self) -> None:
        """Start the bot."""
        print("Starting CryBB Maker Bot...")
        
        # Start health server in background thread
        def run_health_server():
            import uvicorn
            from .server import app
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
