#!/usr/bin/env python3
"""
Debug script for CryBB bot startup issues.
Run this on the DigitalOcean droplet to identify initialization problems.
"""
import sys
import os
import traceback
from pathlib import Path

def debug_imports():
    """Test all critical imports."""
    print("=== TESTING IMPORTS ===")
    
    try:
        print("✓ Python version:", sys.version)
        print("✓ Working directory:", os.getcwd())
        print("✓ Python path:", sys.path)
    except Exception as e:
        print(f"✗ Basic Python info failed: {e}")
        return False
    
    # Test core imports
    imports_to_test = [
        ("src.config", "Config"),
        ("src.twitter_factory", "make_twitter_client"),
        ("src.image_processor", "ImageProcessor"),
        ("src.rate_limiter", "RateLimiter"),
        ("src.per_user_limiter", "PerUserLimiter"),
        ("src.storage", "Storage"),
        ("src.pipeline.orchestrator", "Orchestrator"),
        ("src.batch_context", "ProcessingContext"),
        ("src.server", "app"),
        ("uvicorn", None),
        ("fastapi", None),
        ("requests", None),
        ("requests_oauthlib", None),
        ("PIL", None),
        ("dotenv", None),
    ]
    
    failed_imports = []
    
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name] if class_name else [])
            if class_name:
                getattr(module, class_name)
            print(f"✓ {module_name}" + (f".{class_name}" if class_name else ""))
        except ImportError as e:
            print(f"✗ {module_name}: {e}")
            failed_imports.append(module_name)
        except AttributeError as e:
            print(f"✗ {module_name}.{class_name}: {e}")
            failed_imports.append(f"{module_name}.{class_name}")
        except Exception as e:
            print(f"✗ {module_name}: Unexpected error: {e}")
            failed_imports.append(module_name)
    
    if failed_imports:
        print(f"\n✗ Failed imports: {failed_imports}")
        return False
    else:
        print("\n✓ All imports successful")
        return True

def debug_environment():
    """Test environment variables and configuration."""
    print("\n=== TESTING ENVIRONMENT ===")
    
    try:
        from src.config import Config
        
        # Check required environment variables
        required_vars = [
            "CLIENT_ID", "CLIENT_SECRET", "API_KEY", "API_SECRET",
            "ACCESS_TOKEN", "ACCESS_SECRET", "BEARER_TOKEN"
        ]
        
        missing_vars = []
        for var in required_vars:
            value = getattr(Config, var)
            if not value:
                missing_vars.append(var)
                print(f"✗ {var}: Not set")
            else:
                print(f"✓ {var}: Set (length: {len(value)})")
        
        # Check AI-specific variables
        ai_vars = ["REPLICATE_API_TOKEN", "CRYBB_STYLE_URL"]
        for var in ai_vars:
            value = getattr(Config, var)
            if not value:
                print(f"⚠ {var}: Not set (may be required for AI pipeline)")
            else:
                print(f"✓ {var}: Set")
        
        # Check other important config
        print(f"✓ BOT_HANDLE: {Config.BOT_HANDLE}")
        print(f"✓ TWITTER_MODE: {Config.TWITTER_MODE}")
        print(f"✓ IMAGE_PIPELINE: {Config.IMAGE_PIPELINE}")
        print(f"✓ PORT: {Config.PORT}")
        
        if missing_vars:
            print(f"\n✗ Missing required environment variables: {missing_vars}")
            return False
        else:
            print("\n✓ All required environment variables present")
            return True
            
    except Exception as e:
        print(f"✗ Environment test failed: {e}")
        traceback.print_exc()
        return False

def debug_twitter_client():
    """Test Twitter client initialization."""
    print("\n=== TESTING TWITTER CLIENT ===")
    
    try:
        from src.twitter_factory import make_twitter_client
        
        print("Creating Twitter client...")
        client = make_twitter_client()
        print(f"✓ Twitter client created: {type(client).__name__}")
        
        print("Getting bot identity...")
        bot_id, bot_handle = client.get_bot_identity()
        print(f"✓ Bot identity: @{bot_handle} (ID: {bot_id})")
        
        print("Testing rate limit status...")
        rate_status = client.get_rate_limit_status()
        print(f"✓ Rate limit status: {rate_status}")
        
        return True
        
    except Exception as e:
        print(f"✗ Twitter client test failed: {e}")
        traceback.print_exc()
        return False

def debug_bot_initialization():
    """Test bot initialization."""
    print("\n=== TESTING BOT INITIALIZATION ===")
    
    try:
        from src.main import CryBBBot
        
        print("Creating CryBBBot instance...")
        bot = CryBBBot()
        print("✓ CryBBBot instance created successfully")
        
        print(f"✓ Bot ID: {bot.bot_id}")
        print(f"✓ Bot handle: @{bot.bot_handle}")
        
        return True
        
    except Exception as e:
        print(f"✗ Bot initialization failed: {e}")
        traceback.print_exc()
        return False

def debug_health_server():
    """Test health server startup."""
    print("\n=== TESTING HEALTH SERVER ===")
    
    try:
        from src.server import app
        from src.config import Config
        
        print(f"✓ FastAPI app created")
        print(f"✓ Health server configured for port {Config.PORT}")
        
        # Test if we can create the app without starting it
        print("✓ Health server components ready")
        
        return True
        
    except Exception as e:
        print(f"✗ Health server test failed: {e}")
        traceback.print_exc()
        return False

def debug_file_permissions():
    """Check file permissions and paths."""
    print("\n=== TESTING FILE PERMISSIONS ===")
    
    try:
        # Check working directory
        cwd = os.getcwd()
        print(f"✓ Working directory: {cwd}")
        
        # Check if we can write to outbox
        outbox_path = Path("outbox")
        if outbox_path.exists():
            print(f"✓ Outbox directory exists: {outbox_path.absolute()}")
            try:
                test_file = outbox_path / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
                print("✓ Can write to outbox directory")
            except Exception as e:
                print(f"✗ Cannot write to outbox: {e}")
        else:
            print(f"⚠ Outbox directory does not exist: {outbox_path.absolute()}")
        
        # Check .env file
        env_path = Path(".env")
        if env_path.exists():
            print(f"✓ .env file exists: {env_path.absolute()}")
            print(f"✓ .env file readable: {os.access(env_path, os.R_OK)}")
        else:
            print(f"✗ .env file missing: {env_path.absolute()}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ File permissions test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all debug tests."""
    print("CryBB Bot Startup Debug Script")
    print("=" * 50)
    
    tests = [
        ("File Permissions", debug_file_permissions),
        ("Imports", debug_imports),
        ("Environment", debug_environment),
        ("Twitter Client", debug_twitter_client),
        ("Bot Initialization", debug_bot_initialization),
        ("Health Server", debug_health_server),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            traceback.print_exc()
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("DEBUG SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✓ All tests passed! Bot should be able to start.")
        print("\nIf the bot still doesn't work, try running:")
        print("  python3 -m src.main")
    else:
        print("\n✗ Some tests failed. Fix the issues above before starting the bot.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



