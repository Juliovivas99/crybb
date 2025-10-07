#!/usr/bin/env bash
set -e

# Configuration
APP_DIR=/opt/crybb-bot
SERVICE_NAME=crybb-bot

echo "🔄 Updating CryBB Bot..."

# Navigate to app directory
cd $APP_DIR

# Pull latest changes
echo "📥 Pulling latest changes from repository..."
sudo git pull

# Update Python dependencies
echo "📚 Updating Python dependencies..."
sudo $APP_DIR/venv/bin/pip install -U pip
sudo $APP_DIR/venv/bin/pip install -r requirements.txt

# Restart service
echo "🔄 Restarting service..."
sudo systemctl restart $SERVICE_NAME.service

# Check service status
echo "📊 Checking service status..."
sudo systemctl status $SERVICE_NAME.service --no-pager

echo "✅ Update complete!"
echo ""
echo "Check logs with: journalctl -u $SERVICE_NAME -f"
