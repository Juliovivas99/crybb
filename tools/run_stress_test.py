#!/usr/bin/env python3
"""
Simple runner for the verification stress test.
"""
import asyncio
import sys
import os

# Add tools to path
sys.path.insert(0, os.path.dirname(__file__))

from stress_test_verification import VerificationStressTest

async def run_test():
    """Run the stress test."""
    print("🧪 Starting CryBB Bot Verification Stress Test")
    print("This will simulate 100 mentions in dry run mode")
    print("Press Ctrl+C to cancel\n")
    
    stress_test = VerificationStressTest()
    await stress_test.run_stress_test(100)

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\n👋 Test cancelled by user")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
