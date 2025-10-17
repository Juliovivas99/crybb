#!/bin/bash
set -e

# Configuration
DROPLET_IP="104.236.218.176"
APP_DIR="/opt/crybb-bot"
LOCAL_PROJECT_DIR="/Users/juliovivas/Vscode/crybb"

echo "🚀 Deploying CryBB Bot to DigitalOcean Droplet ($DROPLET_IP)..."

# Step 1: Copy project to droplet
echo "📦 Copying project files to droplet..."
scp -r "$LOCAL_PROJECT_DIR" root@$DROPLET_IP:/opt/crybb-bot

# Step 2: Run deployment commands on droplet
echo "🔧 Setting up environment on droplet..."
ssh root@$DROPLET_IP << 'EOF'
set -e

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Python 3.11 and dependencies
echo "🐍 Installing Python 3.11 and dependencies..."
apt install python3.11 python3.11-venv python3.11-dev python3-pip git curl wget build-essential -y

# Install image processing dependencies
echo "🖼️ Installing image processing dependencies..."
apt install libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev libfribidi-dev libxcb1-dev -y

# Navigate to project directory
cd /opt/crybb-bot

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Verify casino message is correct
echo "🎰 Verifying casino message..."
if grep -q "Welcome to \$CRYBB @{target_username} 🍼" src/main.py; then
    echo "✅ Casino message is correct!"
else
    echo "❌ Casino message not found or incorrect!"
    exit 1
fi

# Copy environment file
echo "🔐 Setting up environment file..."
cp env.example .env
echo "⚠️ Please edit .env file with your actual credentials:"
echo "   nano .env"

# Set up systemd service
echo "⚙️ Setting up systemd service..."
cp scripts/crybb-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable crybb-bot

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials: nano .env"
echo "2. Start the service: systemctl start crybb-bot"
echo "3. Check status: systemctl status crybb-bot"
echo "4. View logs: journalctl -u crybb-bot -f"
EOF

echo "✅ Deployment script completed!"
echo ""
echo "To complete the deployment:"
echo "1. SSH into the droplet: ssh root@$DROPLET_IP"
echo "2. Edit the .env file: cd /opt/crybb-bot && nano .env"
echo "3. Start the service: systemctl start crybb-bot"
echo "4. Check status: systemctl status crybb-bot --no-pager"
