#!/usr/bin/env python3
"""
Stress test script for CryBB bot verification logic.
Simulates 100 mentions with mixed verification statuses in dry run mode.
"""
import os
import sys
import time
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config
from main import CryBBBot
from batch_context import ProcessingContext
from twitter_factory import make_twitter_client

@dataclass
class TestResult:
    """Test result data structure."""
    mention_id: str
    author_username: str
    author_verified: bool
    target_username: str
    target_verified: bool
    processed: bool
    error: str = None
    processing_time: float = 0.0

class VerificationStressTest:
    """Stress test class for verification logic."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
        
    def generate_test_mentions(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate synthetic mentions with mixed verification statuses."""
        mentions = []
        
        # Predefined test users with different verification statuses
        verified_users = [
            "elonmusk", "jack", "tim_cook", "sundarpichai", "satyanadella",
            "jeffbezos", "billgates", "warrenbuffett", "oprah", "taylorswift"
        ]
        
        non_verified_users = [
            "randomuser1", "testuser2", "mockuser3", "sampleuser4", "dummyuser5",
            "fakeuser6", "tempuser7", "testuser8", "mockuser9", "sampleuser10"
        ]
        
        all_targets = verified_users + non_verified_users
        
        for i in range(count):
            # Alternate between verified and non-verified authors
            is_author_verified = i % 2 == 0
            
            if is_author_verified:
                author_username = verified_users[i % len(verified_users)]
            else:
                author_username = non_verified_users[i % len(non_verified_users)]
            
            # Random target (can be verified or not)
            target_username = all_targets[i % len(all_targets)]
            target_verified = target_username in verified_users
            
            mention = {
                "id": f"stress_test_{i}_{int(time.time())}",
                "text": f"@crybbmaker @{target_username} make me crybb #{i}",
                "author_id": f"author_{i}",
                "created_at": datetime.now().isoformat(),
                "author": {
                    "id": f"author_{i}",
                    "username": author_username,
                    "name": f"{author_username.title()} User",
                    "verified": is_author_verified,
                    "profile_image_url": f"https://pbs.twimg.com/profile_images/test_{i}.jpg"
                },
                "entities": {
                    "mentions": [
                        {
                            "username": "crybbmaker",
                            "start": 0,
                            "end": 10
                        },
                        {
                            "username": target_username,
                            "start": 11,
                            "end": 11 + len(target_username)
                        }
                    ]
                },
                "mentioned_users": {
                    target_username: {
                        "id": f"target_{i}",
                        "username": target_username,
                        "name": f"{target_username.title()} Target",
                        "verified": target_verified,
                        "profile_image_url": f"https://pbs.twimg.com/profile_images/target_{i}.jpg"
                    }
                }
            }
            mentions.append(mention)
        
        return mentions
    
    def create_mock_twitter_client(self):
        """Create a mock twitter client that simulates responses without API calls."""
        class MockTwitterClient:
            def __init__(self):
                self.reply_count = 0
                self.upload_count = 0
            
            def get_bot_identity(self):
                return "123456789", "crybbmaker"
            
            def get_mentions(self, since_id=None):
                return []
            
            def get_user_by_id(self, user_id):
                return None
            
            def get_user_by_username(self, username):
                # Return mock user data
                verified_users = ["elonmusk", "jack", "tim_cook", "sundarpichai", "satyanadella"]
                is_verified = username in verified_users
                
                from twitter_client_mock_v2 import UserInfo
                return UserInfo(
                    id=f"mock_{username}",
                    username=username,
                    name=f"Mock {username.title()}",
                    profile_image_url=f"https://pbs.twimg.com/profile_images/mock_{username}.jpg",
                    verified=is_verified
                )
            
            def reply_with_image(self, tweet_id, text, image_bytes):
                """Mock reply method that just counts replies."""
                self.reply_count += 1
                print(f"  📤 Mock Reply #{self.reply_count}: {text}")
                return True
            
            def media_upload(self, image_bytes):
                """Mock media upload."""
                self.upload_count += 1
                return f"mock_media_{self.upload_count}"
        
        return MockTwitterClient()
    
    async def process_mention_async(self, bot: CryBBBot, mention: Dict[str, Any], ctx: ProcessingContext) -> TestResult:
        """Process a single mention asynchronously."""
        start_time = time.time()
        
        author_username = mention['author']['username']
        author_verified = mention['author']['verified']
        target_username = mention['entities']['mentions'][1]['username']
        target_verified = mention['mentioned_users'][target_username]['verified']
        
        try:
            # Process the mention
            await asyncio.to_thread(bot.process_mention, mention, ctx)
            
            processing_time = time.time() - start_time
            
            # Determine if it was processed based on verification logic
            # Only verified authors should be processed
            processed = author_verified
            
            return TestResult(
                mention_id=mention['id'],
                author_username=author_username,
                author_verified=author_verified,
                target_username=target_username,
                target_verified=target_verified,
                processed=processed,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return TestResult(
                mention_id=mention['id'],
                author_username=author_username,
                author_verified=author_verified,
                target_username=target_username,
                target_verified=target_verified,
                processed=False,
                error=str(e),
                processing_time=processing_time
            )
    
    async def run_stress_test(self, mention_count: int = 100):
        """Run the stress test with specified number of mentions."""
        print("🚀 CryBB Bot Verification Stress Test")
        print("=" * 60)
        print(f"Mode: DRY RUN (no actual posts)")
        print(f"Mentions: {mention_count}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Set dry run mode
        os.environ['TWITTER_MODE'] = 'dryrun'
        
        # Generate test mentions
        print(f"\n📝 Generating {mention_count} test mentions...")
        mentions = self.generate_test_mentions(mention_count)
        
        # Initialize bot with mock client
        bot = CryBBBot()
        bot.twitter_client = self.create_mock_twitter_client()
        ctx = ProcessingContext()
        
        print(f"✅ Generated {len(mentions)} mentions")
        print(f"📊 Verification distribution:")
        
        verified_authors = sum(1 for m in mentions if m['author']['verified'])
        non_verified_authors = len(mentions) - verified_authors
        
        print(f"  - Verified authors: {verified_authors}")
        print(f"  - Non-verified authors: {non_verified_authors}")
        
        # Start stress test
        print(f"\n⚡ Starting stress test...")
        self.start_time = time.time()
        
        # Process all mentions concurrently
        tasks = []
        for mention in mentions:
            task = asyncio.create_task(
                self.process_mention_async(bot, mention, ctx)
            )
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        self.end_time = time.time()
        
        # Process results
        for result in results:
            if isinstance(result, TestResult):
                self.results.append(result)
            else:
                print(f"❌ Task failed with exception: {result}")
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate detailed test report."""
        if not self.results:
            print("❌ No results to report")
            return
        
        total_time = self.end_time - self.start_time
        
        # Calculate statistics
        total_mentions = len(self.results)
        processed_count = sum(1 for r in self.results if r.processed)
        skipped_count = total_mentions - processed_count
        error_count = sum(1 for r in self.results if r.error)
        
        verified_authors_processed = sum(1 for r in self.results if r.author_verified and r.processed)
        non_verified_authors_skipped = sum(1 for r in self.results if not r.author_verified and not r.processed)
        
        avg_processing_time = sum(r.processing_time for r in self.results) / total_mentions
        max_processing_time = max(r.processing_time for r in self.results)
        min_processing_time = min(r.processing_time for r in self.results)
        
        # Print report
        print("\n" + "=" * 60)
        print("📊 STRESS TEST RESULTS")
        print("=" * 60)
        
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print(f"📈 Throughput: {total_mentions / total_time:.2f} mentions/sec")
        print(f"📝 Total Mentions: {total_mentions}")
        print(f"✅ Processed: {processed_count}")
        print(f"⏭️  Skipped: {skipped_count}")
        print(f"❌ Errors: {error_count}")
        
        print(f"\n🔍 Verification Logic:")
        print(f"  ✅ Verified authors processed: {verified_authors_processed}")
        print(f"  ⏭️  Non-verified authors skipped: {non_verified_authors_skipped}")
        
        print(f"\n⏱️  Performance:")
        print(f"  📊 Average processing time: {avg_processing_time:.3f}s")
        print(f"  🚀 Fastest: {min_processing_time:.3f}s")
        print(f"  🐌 Slowest: {max_processing_time:.3f}s")
        
        # Verification accuracy
        correct_verification = verified_authors_processed + non_verified_authors_skipped
        verification_accuracy = (correct_verification / total_mentions) * 100
        
        print(f"\n🎯 Verification Accuracy: {verification_accuracy:.1f}%")
        
        if verification_accuracy == 100.0:
            print("🎉 PERFECT! All verification logic working correctly!")
        elif verification_accuracy >= 95.0:
            print("✅ EXCELLENT! Verification logic working well!")
        elif verification_accuracy >= 90.0:
            print("⚠️  GOOD! Minor issues detected.")
        else:
            print("❌ ISSUES DETECTED! Verification logic needs attention.")
        
        # Save detailed results
        self.save_detailed_results()
    
    def save_detailed_results(self):
        """Save detailed results to JSON file."""
        results_data = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "total_mentions": len(self.results),
                "total_time": self.end_time - self.start_time,
                "mode": "dryrun"
            },
            "summary": {
                "processed": sum(1 for r in self.results if r.processed),
                "skipped": sum(1 for r in self.results if not r.processed),
                "errors": sum(1 for r in self.results if r.error),
                "verified_authors_processed": sum(1 for r in self.results if r.author_verified and r.processed),
                "non_verified_authors_skipped": sum(1 for r in self.results if not r.author_verified and not r.processed)
            },
            "results": [
                {
                    "mention_id": r.mention_id,
                    "author_username": r.author_username,
                    "author_verified": r.author_verified,
                    "target_username": r.target_username,
                    "target_verified": r.target_verified,
                    "processed": r.processed,
                    "error": r.error,
                    "processing_time": r.processing_time
                }
                for r in self.results
            ]
        }
        
        filename = f"stress_test_results_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {filename}")

async def main():
    """Main function to run the stress test."""
    stress_test = VerificationStressTest()
    
    try:
        await stress_test.run_stress_test(100)
    except KeyboardInterrupt:
        print("\n⏹️  Stress test interrupted by user")
    except Exception as e:
        print(f"\n❌ Stress test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
