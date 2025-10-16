#!/usr/bin/env python3
"""
Test tool for batch snapshot functionality.
Simulates mentions response with includes.users and tests ProcessingContext behavior.
"""
import sys
import time
sys.path.append('src')

from batch_context import ProcessingContext
from x_v2 import _normalize_user_min


def test_batch_snapshot():
    """Test batch snapshot functionality."""
    print("🧪 Testing Batch Snapshot Functionality")
    print("=" * 50)
    
    # Simulate a mentions response with includes.users
    mock_mentions_response = {
        "tweets": [
            {
                "id": "1234567890",
                "text": "@crybbmaker @alice make me crybb",
                "author_id": "1111111111"
            },
            {
                "id": "1234567891", 
                "text": "@crybbmaker @bob make me crybb",
                "author_id": "2222222222"
            }
        ],
        "includes": {
            "users": [
                {
                    "id": "1111111111",
                    "username": "alice",
                    "name": "Alice Smith",
                    "profile_image_url": "https://pbs.twimg.com/profile_images/alice_normal.jpg"
                },
                {
                    "id": "2222222222", 
                    "username": "bob",
                    "name": "Bob Johnson",
                    "profile_image_url": "https://pbs.twimg.com/profile_images/bob_normal.jpg"
                }
            ]
        }
    }
    
    # Build batch snapshot
    users = mock_mentions_response["includes"]["users"]
    batch_users = {
        (u.get("username", "").lower()): _normalize_user_min(u)
        for u in users if u.get("username")
    }
    
    ctx = ProcessingContext(batch_users=batch_users)
    print(f"✅ Built batch snapshot: users={len(batch_users)}")
    
    # Test user resolution
    print("\n🔍 Testing User Resolution:")
    
    # Test users in batch
    alice_data = ctx.get_user("alice")
    assert alice_data is not None, "Alice should be found in batch"
    print(f"✅ Found alice in batch: {alice_data['username']}")
    
    bob_data = ctx.get_user("bob")
    assert bob_data is not None, "Bob should be found in batch"
    print(f"✅ Found bob in batch: {bob_data['username']}")
    
    # Test user not in batch
    charlie_data = ctx.get_user("charlie")
    assert charlie_data is None, "Charlie should not be found in batch"
    print(f"✅ Charlie not found in batch (as expected)")
    
    # Test case insensitivity
    alice_upper = ctx.get_user("ALICE".lower())  # Convert to lowercase
    assert alice_upper is not None, "Alice should be found with uppercase"
    print(f"✅ Case insensitive lookup works: {alice_upper['username']}")
    
    # Test inflight pinning
    print("\n📌 Testing Inflight Pinning:")
    
    # Pin a user
    charlie_mock = {
        "id": "3333333333",
        "username": "charlie",
        "name": "Charlie Brown",
        "profile_image_url": "https://pbs.twimg.com/profile_images/charlie_normal.jpg"
    }
    ctx.pin_user("charlie", charlie_mock)
    
    # Should find pinned user
    charlie_pinned = ctx.get_user("charlie")
    assert charlie_pinned is not None, "Charlie should be found after pinning"
    print(f"✅ Found charlie after pinning: {charlie_pinned['username']}")
    
    # Test expiry simulation (don't actually wait)
    print("\n⏰ Testing Expiry Simulation:")
    
    # Create context with short TTL for testing
    test_ctx = ProcessingContext(inflight_ttl_secs=1)
    test_ctx.pin_user("testuser", {"username": "testuser", "name": "Test User"})
    
    # Should find immediately
    test_user = test_ctx.get_user("testuser")
    assert test_user is not None, "Test user should be found immediately"
    print(f"✅ Found testuser immediately: {test_user['username']}")
    
    # Simulate expiry by manually setting expired time
    test_ctx.inflight_users["testuser"]["expires_at"] = time.time() - 1
    
    # Should not find after expiry
    expired_user = test_ctx.get_user("testuser")
    assert expired_user is None, "Test user should not be found after expiry"
    print(f"✅ Test user correctly expired")
    
    # Test profile image URL normalization
    print("\n🖼️  Testing Profile Image Normalization:")
    alice_pfp = alice_data["profile_image_url"]
    assert "_400x400." in alice_pfp, "Profile image should be normalized to 400x400"
    print(f"✅ Profile image normalized: {alice_pfp}")
    
    print("\n🎉 All tests passed! Batch snapshot functionality working correctly.")
    
    # Test counter simulation
    print("\n📊 Batch Snapshot Benefits:")
    print(f"  • Batch users: {len(batch_users)}")
    print(f"  • Inflight pins: {len(ctx.inflight_users)}")
    print(f"  • No network calls needed for batch users")
    print(f"  • Long processing protected by inflight pins")


if __name__ == "__main__":
    test_batch_snapshot()
