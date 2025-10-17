#!/bin/bash
# Quick deployment script for CryBB bot fixes
# Deploy debug tools and improved error handling to DigitalOcean droplet

set -e

DROPLET_IP="64.225.24.163"
DROPLET_USER="root"
BOT_DIR="/opt/crybb-bot"

echo "=== Deploying CryBB Bot Fixes ==="
echo "Target: $DROPLET_USER@$DROPLET_IP:$BOT_DIR"
echo

# Files to deploy
FILES=(
    "debug_startup.py"
    "scripts/debug_and_fix.sh"
    "src/main.py"
    "DEBUG_STARTUP_GUIDE.md"
)

echo "Deploying files..."
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Deploying $file..."
        scp "$file" "$DROPLET_USER@$DROPLET_IP:$BOT_DIR/"
    else
        echo "Warning: $file not found, skipping"
    fi
done

echo
echo "Making debug script executable..."
ssh "$DROPLET_USER@$DROPLET_IP" "chmod +x $BOT_DIR/scripts/debug_and_fix.sh"

echo
echo "=== Deployment Complete ==="
echo
echo "Next steps on the droplet:"
echo "1. Run debug script: sudo $BOT_DIR/scripts/debug_and_fix.sh"
echo "2. Or run Python debug: cd $BOT_DIR && python3 debug_startup.py"
echo "3. Check logs: journalctl -u crybb-bot -f"
echo
echo "Files deployed:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done



