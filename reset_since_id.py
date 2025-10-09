#!/usr/bin/env python3
"""
Reset since_id to fetch all recent mentions
"""
import json
import os

# Reset since_id to None to fetch all recent mentions
since_id_file = "outbox/since_id.json"
if os.path.exists(since_id_file):
    os.remove(since_id_file)
    print("✅ Removed since_id.json - bot will fetch all recent mentions")
else:
    print("ℹ️  No since_id.json found")

# Also check what the current since_id was
print(f"Previous since_id was: 1938507397787521334")
print("This means the bot was only looking for mentions after that tweet ID")
print("Now it will fetch all recent mentions")

