#!/usr/bin/env python3
"""
No-post simulation that runs PFPs through the nano-banana pipeline.
Generates CryBB images and shows exact Twitter reply payloads without posting.
"""
import sys
import os
import json
import time
from datetime import datetime
sys.path.append('src')

from config import Config
from pipeline.orchestrator import Orchestrator
from twitter_factory import make_twitter_client

# Test PFP URLs provided by user
TEST_PFP_URLS = [
    "https://pbs.twimg.com/profile_images/1975699930543951872/ektsy7PJ_400x400.jpg",
    "https://pbs.twimg.com/profile_images/1673462694832140290/r1OCau5P_400x400.jpg", 
    "https://pbs.twimg.com/profile_images/1937179802290561024/5cjt-zs0_400x400.jpg",
    "https://pbs.twimg.com/profile_images/1926595777322688513/ph0tlmgJ_400x400.jpg"
]

def simulate_pfp_processing():
    """Run PFPs through the pipeline and show what would be posted."""
    print("🎭 CryBB PFP Pipeline Simulation")
    print("=" * 50)
    print(f"Processing {len(TEST_PFP_URLS)} test PFPs...")
    print(f"Style URL: {Config.CRYBB_STYLE_URL}")
    print(f"Pipeline: {Config.IMAGE_PIPELINE}")
    print()
    
    # Initialize components
    orchestrator = Orchestrator(Config)
    client = make_twitter_client()
    
    # Create output directory
    output_dir = "simulation_output"
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    for i, pfp_url in enumerate(TEST_PFP_URLS, 1):
        print(f"🔄 Processing PFP {i}/{len(TEST_PFP_URLS)}")
        print(f"   URL: {pfp_url}")
        
        try:
            # Generate CryBB image
            start_time = time.time()
            image_bytes = orchestrator.render_with_urls(
                [Config.CRYBB_STYLE_URL, pfp_url],
                mention_text="make me crybb"
            )
            generation_time = time.time() - start_time
            
            # Save generated image
            output_filename = f"crybb_output_{i}.jpg"
            output_path = os.path.join(output_dir, output_filename)
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            
            # Simulate media upload (dry run)
            print(f"   📸 Generated image: {len(image_bytes)} bytes")
            print(f"   ⏱️  Generation time: {generation_time:.2f}s")
            print(f"   💾 Saved to: {output_path}")
            
            # Create mock tweet data
            mock_tweet_id = f"mock_tweet_{int(time.time())}_{i}"
            mock_username = f"testuser{i}"
            
            # Create reply payload
            reply_text = ""  # No text content to avoid repetitive content detection
            
            # Simulate what would be uploaded to Twitter
            mock_media_id = f"mock_media_{i}_{int(time.time())}"
            
            # Create Twitter API payload
            twitter_payload = {
                "text": reply_text,
                "reply": {
                    "in_reply_to_tweet_id": mock_tweet_id
                },
                "media": {
                    "media_ids": [mock_media_id]
                }
            }
            
            result = {
                "pfp_url": pfp_url,
                "generated_image_path": output_path,
                "image_size_bytes": len(image_bytes),
                "generation_time_seconds": generation_time,
                "reply_text": reply_text,
                "twitter_payload": twitter_payload,
                "mock_tweet_id": mock_tweet_id,
                "mock_media_id": mock_media_id
            }
            
            results.append(result)
            
            print(f"   ✅ Success!")
            print(f"   📝 Reply text: {reply_text}")
            print(f"   🐦 Media ID: {mock_media_id}")
            print()
            
        except Exception as e:
            print(f"   ❌ Error processing PFP {i}: {e}")
            print()
    
    # Generate summary report
    print("📊 SIMULATION SUMMARY")
    print("=" * 50)
    print(f"Total PFPs processed: {len(results)}")
    print(f"Successful generations: {len([r for r in results if 'generated_image_path' in r])}")
    print(f"Total generation time: {sum(r.get('generation_time_seconds', 0) for r in results):.2f}s")
    print(f"Average generation time: {sum(r.get('generation_time_seconds', 0) for r in results) / len(results):.2f}s")
    print()
    
    # Show all Twitter payloads
    print("🐦 TWITTER REPLY PAYLOADS")
    print("=" * 50)
    for i, result in enumerate(results, 1):
        if 'twitter_payload' in result:
            print(f"Reply {i}:")
            print(f"  Tweet ID: {result['mock_tweet_id']}")
            print(f"  Text: {result['reply_text']}")
            print(f"  Media ID: {result['mock_media_id']}")
            print(f"  Full Payload:")
            print(f"    {json.dumps(result['twitter_payload'], indent=6)}")
            print()
    
    # Save detailed results
    results_file = os.path.join(output_dir, "simulation_results.json")
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "config": {
                "style_url": Config.CRYBB_STYLE_URL,
                "pipeline": Config.IMAGE_PIPELINE,
                "model": Config.REPLICATE_MODEL
            },
            "results": results
        }, f, indent=2)
    
    print(f"📁 All results saved to: {output_dir}/")
    print(f"📄 Detailed results: {results_file}")
    print()
    print("🎉 Simulation complete! Check the generated images and payloads.")

if __name__ == "__main__":
    try:
        simulate_pfp_processing()
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        sys.exit(1)
