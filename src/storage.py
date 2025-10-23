"""
Simple storage for persisting since_id and processed tweet IDs across runs.
"""
import json
import os
import time
import fcntl
import threading
from typing import Optional, Set, Dict, Tuple
from src.config import Config


class Storage:
    """Simple file-based storage for since_id and processed tweet ID persistence."""
    
    def __init__(self):
        """Initialize storage."""
        self.storage_file = os.path.join(Config.OUTBOX_DIR, "since_id.json")
        self.processed_ids_file = os.path.join(Config.OUTBOX_DIR, "processed_ids.json")
        self.conversation_cache_file = os.path.join(Config.OUTBOX_DIR, "conversation_cache.json")
        self.processed_conversations_file = os.path.join(Config.OUTBOX_DIR, "processed_conversations.json")
        os.makedirs(Config.OUTBOX_DIR, exist_ok=True)
        
        # In-memory conversation cache with TTL
        self._conversation_cache: Dict[Tuple[str, str], float] = {}
        self._conversation_cache_ttl = 45 * 60  # 45 minutes
        self._load_conversation_cache()
        
        # In-memory processed conversations set for conversation-level deduplication
        self._processed_conversations: Set[str] = set()
        self._load_processed_conversations()
        
        # Thread lock for file operations
        self._file_lock = threading.Lock()
    
    def read_since_id(self) -> Optional[str]:
        """Read since_id from storage file."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, "r") as f:
                    data = json.load(f)
                    return data.get("since_id")
        except Exception as e:
            print(f"Error reading since_id: {e}")
        
        return None
    
    def write_since_id(self, since_id: str) -> None:
        """Atomically write since_id to storage file."""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            data = {"since_id": since_id}
            tmp = f"{self.storage_file}.tmp"
            with open(tmp, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, self.storage_file)  # atomic on POSIX
        except Exception as e:
            print(f"Error writing since_id: {e}")
    
    def read_processed_ids(self) -> Set[str]:
        """Read processed tweet IDs from storage file."""
        try:
            if os.path.exists(self.processed_ids_file):
                with open(self.processed_ids_file, "r") as f:
                    data = json.load(f)
                    return set(data.get("processed_ids", []))
        except Exception as e:
            print(f"Error reading processed_ids: {e}")
        
        return set()
    
    def mark_processed(self, tweet_id: str) -> bool:
        """
        Atomically mark a tweet as processed.
        
        Args:
            tweet_id: The tweet ID to mark as processed
            
        Returns:
            bool: True if successfully marked as processed, False if already processed
        """
        with self._file_lock:
            try:
                os.makedirs(os.path.dirname(self.processed_ids_file), exist_ok=True)
                
                # Use file locking for atomic read-modify-write
                lock_file_path = f"{self.processed_ids_file}.lock"
                
                with open(lock_file_path, 'w') as lock_file:
                    # Acquire exclusive file lock
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                    
                    try:
                        # Read current processed IDs
                        current = set()
                        if os.path.exists(self.processed_ids_file):
                            with open(self.processed_ids_file, "r") as f:
                                data = json.load(f)
                                current = set(data.get("processed_ids", []))
                        
                        # Check if already processed
                        if tweet_id in current:
                            return False  # Already processed
                        
                        # Add new tweet ID
                        current.add(tweet_id)
                        
                        # Write atomically using temp file + rename
                        tmp_file = f"{self.processed_ids_file}.tmp"
                        with open(tmp_file, "w") as f:
                            json.dump({"processed_ids": sorted(list(current))}, f, indent=2)
                        
                        # Atomic rename (POSIX guarantee)
                        os.replace(tmp_file, self.processed_ids_file)
                        
                        return True  # Successfully marked as processed
                        
                    finally:
                        # Release file lock
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                        
            except Exception as e:
                print(f"Error marking {tweet_id} processed: {e}")
                return False
            finally:
                # Clean up lock file
                try:
                    if os.path.exists(lock_file_path):
                        os.remove(lock_file_path)
                except:
                    pass
    
    def is_processed(self, tweet_id: str) -> bool:
        """Check if a tweet ID has been processed."""
        return tweet_id in self.read_processed_ids()
    
    def is_processing(self, tweet_id: str) -> bool:
        """
        Check if a tweet is currently being processed by checking for a processing lock file.
        
        Args:
            tweet_id: The tweet ID to check
            
        Returns:
            bool: True if tweet is currently being processed, False otherwise
        """
        processing_lock_file = os.path.join(Config.OUTBOX_DIR, f"processing_{tweet_id}.lock")
        return os.path.exists(processing_lock_file)
    
    def acquire_processing_lock(self, tweet_id: str) -> bool:
        """
        Acquire a processing lock for a tweet to prevent concurrent processing.
        
        Args:
            tweet_id: The tweet ID to acquire lock for
            
        Returns:
            bool: True if lock acquired successfully, False if already being processed
        """
        processing_lock_file = os.path.join(Config.OUTBOX_DIR, f"processing_{tweet_id}.lock")
        
        try:
            # Check if already being processed
            if os.path.exists(processing_lock_file):
                return False
            
            # Create processing lock file
            os.makedirs(os.path.dirname(processing_lock_file), exist_ok=True)
            with open(processing_lock_file, 'w') as f:
                f.write(str(time.time()))  # Write timestamp for debugging
            return True
            
        except Exception as e:
            print(f"Error acquiring processing lock for {tweet_id}: {e}")
            return False
    
    def release_processing_lock(self, tweet_id: str) -> None:
        """
        Release a processing lock for a tweet.
        
        Args:
            tweet_id: The tweet ID to release lock for
        """
        processing_lock_file = os.path.join(Config.OUTBOX_DIR, f"processing_{tweet_id}.lock")
        
        try:
            if os.path.exists(processing_lock_file):
                os.remove(processing_lock_file)
        except Exception as e:
            print(f"Error releasing processing lock for {tweet_id}: {e}")
    
    def cleanup_stale_processing_locks(self, max_age_seconds: int = 300) -> None:
        """
        Clean up stale processing lock files that may have been left behind by crashed processes.
        
        Args:
            max_age_seconds: Maximum age in seconds for processing locks (default 5 minutes)
        """
        try:
            outbox_dir = Config.OUTBOX_DIR
            if not os.path.exists(outbox_dir):
                return
            
            current_time = time.time()
            cleaned_count = 0
            
            for filename in os.listdir(outbox_dir):
                if filename.startswith("processing_") and filename.endswith(".lock"):
                    lock_file_path = os.path.join(outbox_dir, filename)
                    
                    try:
                        # Check file age
                        file_age = current_time - os.path.getmtime(lock_file_path)
                        if file_age > max_age_seconds:
                            os.remove(lock_file_path)
                            cleaned_count += 1
                            print(f"Cleaned up stale processing lock: {filename}")
                    except Exception as e:
                        print(f"Error cleaning up lock file {filename}: {e}")
            
            if cleaned_count > 0:
                print(f"Cleaned up {cleaned_count} stale processing locks")
                
        except Exception as e:
            print(f"Error during stale lock cleanup: {e}")
    
    def _load_conversation_cache(self) -> None:
        """Load conversation cache from file."""
        try:
            if os.path.exists(self.conversation_cache_file):
                with open(self.conversation_cache_file, "r") as f:
                    data = json.load(f)
                    # Convert string keys back to tuples
                    for key_str, timestamp in data.items():
                        conversation_id, target_username = key_str.split(":", 1)
                        self._conversation_cache[(conversation_id, target_username)] = timestamp
        except Exception as e:
            print(f"Error loading conversation cache: {e}")
    
    def _save_conversation_cache(self) -> None:
        """Save conversation cache to file."""
        try:
            # Convert tuple keys to strings for JSON serialization
            data = {f"{conv_id}:{target}": timestamp 
                   for (conv_id, target), timestamp in self._conversation_cache.items()}
            
            tmp = f"{self.conversation_cache_file}.tmp"
            with open(tmp, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, self.conversation_cache_file)  # atomic on POSIX
        except Exception as e:
            print(f"Error saving conversation cache: {e}")
    
    def _prune_conversation_cache(self) -> None:
        """Remove expired entries from conversation cache."""
        now = time.time()
        expired_keys = [
            key for key, timestamp in self._conversation_cache.items()
            if now - timestamp > self._conversation_cache_ttl
        ]
        for key in expired_keys:
            del self._conversation_cache[key]
    
    def check_conversation_dedupe(self, conversation_id: str, target_username: str) -> bool:
        """
        Check if we've already processed this conversation-target pair recently.
        
        Args:
            conversation_id: The conversation ID
            target_username: The target username (normalized)
            
        Returns:
            True if we should skip (already processed), False if we should proceed
        """
        self._prune_conversation_cache()
        
        key = (conversation_id, target_username.lower())
        now = time.time()
        
        if key in self._conversation_cache:
            timestamp = self._conversation_cache[key]
            if now - timestamp < self._conversation_cache_ttl:
                return True  # Skip - already processed recently
        
        return False  # Proceed
    
    def record_conversation_dedupe(self, conversation_id: str, target_username: str) -> None:
        """
        Record that we've processed this conversation-target pair.
        
        Args:
            conversation_id: The conversation ID
            target_username: The target username (normalized)
        """
        key = (conversation_id, target_username.lower())
        self._conversation_cache[key] = time.time()
        self._save_conversation_cache()
    
    def _load_processed_conversations(self) -> None:
        """Load processed conversations from file."""
        try:
            if os.path.exists(self.processed_conversations_file):
                with open(self.processed_conversations_file, "r") as f:
                    data = json.load(f)
                    self._processed_conversations = set(data.get("processed_conversations", []))
        except Exception as e:
            print(f"Error loading processed conversations: {e}")
    
    def _save_processed_conversations(self) -> None:
        """Save processed conversations to file."""
        try:
            tmp = f"{self.processed_conversations_file}.tmp"
            with open(tmp, "w") as f:
                json.dump({"processed_conversations": sorted(list(self._processed_conversations))}, f, indent=2)
            os.replace(tmp, self.processed_conversations_file)  # atomic on POSIX
        except Exception as e:
            print(f"Error saving processed conversations: {e}")
    
    def is_conversation_processed(self, conversation_id: str) -> bool:
        """
        Check if a conversation has already been processed.
        
        Args:
            conversation_id: The conversation ID to check
            
        Returns:
            bool: True if conversation has been processed, False otherwise
        """
        return conversation_id in self._processed_conversations
    
    def mark_conversation_processed(self, conversation_id: str) -> None:
        """
        Mark a conversation as processed.
        
        Args:
            conversation_id: The conversation ID to mark as processed
        """
        self._processed_conversations.add(conversation_id)
        self._save_processed_conversations()



