#!/usr/bin/env bash
set -e

# Configuration
APP_DIR=/opt/crybb-bot
REPO_URL=git@github.com:YOURUSERNAME/crybb-bot.git
SERVICE_NAME=crybb-bot

echo "🚀 Deploying CryBB Bot to DigitalOcean Droplet..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update

# Install Python 3.11 and dependencies if missing
echo "🐍 Installing Python 3.11 and dependencies..."
sudo apt install -y python3.11 python3.11-venv python3.11-dev git curl build-essential

# Install additional system dependencies for image processing
echo "🖼️ Installing image processing dependencies..."
sudo apt install -y libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev libfribidi-dev libxcb1-dev

# Clone or pull repository
echo "📥 Setting up repository..."
if [ ! -d "$APP_DIR" ]; then
    echo "Cloning repository to $APP_DIR..."
    sudo git clone $REPO_URL $APP_DIR
    sudo chown -R root:root $APP_DIR
else
    echo "Updating existing repository..."
    cd $APP_DIR && sudo git pull
fi

# Set up Python virtual environment
echo "🔧 Setting up Python virtual environment..."
cd $APP_DIR
sudo python3.11 -m venv venv
sudo chown -R root:root venv

# Activate virtual environment and install dependencies
echo "📚 Installing Python dependencies..."
sudo $APP_DIR/venv/bin/pip install -U pip
sudo $APP_DIR/venv/bin/pip install -r requirements.txt

# Copy environment file if provided
if [ -f /tmp/.env ]; then
    echo "🔐 Copying environment file..."
    sudo cp /tmp/.env $APP_DIR/.env
    sudo chown root:root $APP_DIR/.env
    sudo chmod 600 $APP_DIR/.env
else
    echo "⚠️ No .env file found in /tmp/.env"
    echo "Please ensure your .env file is uploaded to the droplet"
fi

# Create systemd service file
echo "⚙️ Setting up systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=CryBB Twitter Bot
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python3 src/main.py
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "🔄 Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME.service
sudo systemctl restart $SERVICE_NAME.service

# Check service status
echo "📊 Checking service status..."
sudo systemctl status $SERVICE_NAME.service --no-pager

echo "✅ Deployment complete!"
echo ""
echo "Useful commands:"
echo "  Check logs:     journalctl -u $SERVICE_NAME -f"
echo "  Restart bot:    sudo systemctl restart $SERVICE_NAME"
echo "  Stop bot:       sudo systemctl stop $SERVICE_NAME"
echo "  Check status:   sudo systemctl status $SERVICE_NAME"
