#!/usr/bin/env python3
"""
Test utility for CryBB Maker Bot mention parsing.
Tests the extract_target_after_bot function with synthetic mention data.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import extract_target_after_bot, normalize_pfp_url

def test_mention_parsing():
    """Test mention parsing with synthetic data."""
    
    # Test case 1: Normal mention with target
    test_data_1 = {
        "data": {
            "id": "123",
            "text": "@crybbmaker @targetuser make me #crybb",
            "entities": {
                "mentions": [
                    {"start": 0, "end": 12, "username": "crybbmaker"},
                    {"start": 13, "end": 25, "username": "targetuser"}
                ]
            },
            "author_id": "111"
        },
        "includes": {
            "users": [
                {"id": "111", "username": "authoruser", "profile_image_url": "https://pbs.twimg.com/profile_images/.../author_400x400.jpg"},
                {"id": "222", "username": "targetuser", "profile_image_url": "https://pbs.twimg.com/profile_images/.../target_400x400.jpg"}
            ]
        }
    }
    
    # Test case 2: Multiple mentions, bot not first
    test_data_2 = {
        "data": {
            "id": "124",
            "text": "Hey @crybbmaker @targetuser @anotheruser make me #crybb",
            "entities": {
                "mentions": [
                    {"start": 4, "end": 16, "username": "crybbmaker"},
                    {"start": 17, "end": 29, "username": "targetuser"},
                    {"start": 30, "end": 42, "username": "anotheruser"}
                ]
            },
            "author_id": "111"
        },
        "includes": {
            "users": [
                {"id": "111", "username": "authoruser", "profile_image_url": "https://pbs.twimg.com/profile_images/.../author_400x400.jpg"},
                {"id": "222", "username": "targetuser", "profile_image_url": "https://pbs.twimg.com/profile_images/.../target_400x400.jpg"},
                {"id": "333", "username": "anotheruser", "profile_image_url": "https://pbs.twimg.com/profile_images/.../another_400x400.jpg"}
            ]
        }
    }
    
    # Test case 3: No target mention, should fallback to author
    test_data_3 = {
        "data": {
            "id": "125",
            "text": "@crybbmaker make me #crybb",
            "entities": {
                "mentions": [
                    {"start": 0, "end": 12, "username": "crybbmaker"}
                ]
            },
            "author_id": "111"
        },
        "includes": {
            "users": [
                {"id": "111", "username": "authoruser", "profile_image_url": "https://pbs.twimg.com/profile_images/.../author_400x400.jpg"}
            ]
        }
    }
    
    # Test case 4: Bot mention not found, should use first non-bot mention
    test_data_4 = {
        "data": {
            "id": "126",
            "text": "@targetuser @anotheruser make me #crybb",
            "entities": {
                "mentions": [
                    {"start": 0, "end": 12, "username": "targetuser"},
                    {"start": 13, "end": 25, "username": "anotheruser"}
                ]
            },
            "author_id": "111"
        },
        "includes": {
            "users": [
                {"id": "111", "username": "authoruser", "profile_image_url": "https://pbs.twimg.com/profile_images/.../author_400x400.jpg"},
                {"id": "222", "username": "targetuser", "profile_image_url": "https://pbs.twimg.com/profile_images/.../target_400x400.jpg"},
                {"id": "333", "username": "anotheruser", "profile_image_url": "https://pbs.twimg.com/profile_images/.../another_400x400.jpg"}
            ]
        }
    }
    
    test_cases = [
        ("Normal mention with target", test_data_1, "targetuser"),
        ("Multiple mentions, bot not first", test_data_2, "targetuser"),
        ("No target mention, fallback to author", test_data_3, "authoruser"),
        ("Bot not mentioned, use first non-bot", test_data_4, "targetuser")
    ]
    
    print("🧪 Testing CryBB Maker Bot Mention Parsing")
    print("=" * 50)
    
    for test_name, test_data, expected_target in test_cases:
        print(f"\n📝 Test: {test_name}")
        print(f"Tweet: {test_data['data']['text']}")
        
        # Extract target
        tweet_data = test_data['data']
        author_username = "authoruser"  # From test data
        target_username = extract_target_after_bot(tweet_data, "crybbmaker", author_username)
        
        print(f"Expected target: {expected_target}")
        print(f"Actual target: {target_username}")
        
        if target_username == expected_target:
            print("✅ PASS")
        else:
            print("❌ FAIL")
            return False
        
        # Test PFP URL normalization if target found
        if target_username and target_username != author_username:
            # Find target user in includes
            target_user = None
            for user in test_data['includes']['users']:
                if user['username'] == target_username:
                    target_user = user
                    break
            
            if target_user:
                original_pfp = target_user['profile_image_url']
                normalized_pfp = normalize_pfp_url(original_pfp)
                print(f"Original PFP: {original_pfp}")
                print(f"Normalized PFP: {normalized_pfp}")
                
                # Check if normalization worked
                if "_400x400." in normalized_pfp:
                    print("✅ PFP normalization works")
                else:
                    print("⚠️  PFP normalization may not be working correctly")
    
    print("\n" + "=" * 50)
    print("🎉 All mention parsing tests passed!")
    return True

def test_with_synthetic_data():
    """Test with the exact synthetic data from the requirements."""
    
    synthetic_mention = {
        "data": {
            "id": "123",
            "text": "@crybbmaker @targetuser make me #crybb",
            "entities": {
                "mentions": [
                    {"start": 0, "end": 12, "username": "crybbmaker"},
                    {"start": 13, "end": 25, "username": "targetuser"}
                ]
            },
            "author_id": "111"
        },
        "includes": {
            "users": [
                {"id": "111", "username": "authoruser", "profile_image_url": "https://pbs.twimg.com/profile_images/.../author_400x400.jpg"},
                {"id": "222", "username": "targetuser", "profile_image_url": "https://pbs.twimg.com/profile_images/.../target_400x400.jpg"}
            ]
        }
    }
    
    print("\n🎯 Testing with exact synthetic data from requirements:")
    print("=" * 50)
    
    tweet_data = synthetic_mention['data']
    author_username = "authoruser"
    target_username = extract_target_after_bot(tweet_data, "crybbmaker", author_username)
    
    print(f"Target selected: {target_username}")
    
    # Find target user and get PFP URL
    target_user = None
    for user in synthetic_mention['includes']['users']:
        if user['username'] == target_username:
            target_user = user
            break
    
    if target_user:
        pfp_url = normalize_pfp_url(target_user['profile_image_url'])
        print(f"PFP URL: {pfp_url}")
    else:
        print("❌ Target user not found in includes")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = test_mention_parsing()
        if success:
            test_with_synthetic_data()
            print("\n🚀 All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        sys.exit(1)
