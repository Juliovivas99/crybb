#!/bin/bash
set -euo pipefail

# CryBB Bot Systemd Fixer Script
# Fixes the systemd unit file and verifies the service works

echo "🔧 Fixing CryBB Bot systemd configuration..."

# Write the corrected unit file
echo "📝 Writing corrected systemd unit file..."
sudo tee /etc/systemd/system/crybb-bot.service > /dev/null << 'EOF'
[Unit]
Description=CryBB Twitter Bot
After=network-online.target
Wants=network-online.target

[Service]
User=root
WorkingDirectory=/root/crybb
EnvironmentFile=/root/crybb/.env
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 -u -m src.main
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=inherit

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and restart service
echo "🔄 Reloading systemd daemon and restarting service..."
sudo systemctl daemon-reload
sudo systemctl restart crybb-bot

# Wait a moment for startup
sleep 5

# Check service status
echo "📊 Checking service status..."
if ! sudo systemctl is-active --quiet crybb-bot; then
    echo "❌ Service is not active!"
    sudo systemctl status crybb-bot
    echo "📋 Recent logs:"
    sudo journalctl -u crybb-bot -n 100 --no-pager
    exit 1
fi

echo "✅ Service is active"

# Check health endpoint
echo "🏥 Checking health endpoint..."
if ! curl -fsS localhost:8000/health > /dev/null; then
    echo "❌ Health endpoint not responding!"
    echo "📋 Recent logs:"
    sudo journalctl -u crybb-bot -n 100 --no-pager
    exit 1
fi

echo "✅ Health endpoint responding"

# Check metrics endpoint
echo "📈 Checking metrics endpoint..."
if ! curl -fsS localhost:8000/metrics > /dev/null; then
    echo "❌ Metrics endpoint not responding!"
    echo "📋 Recent logs:"
    sudo journalctl -u crybb-bot -n 100 --no-pager
    exit 1
fi

echo "✅ Metrics endpoint responding"

# Show final status
echo "🎉 CryBB Bot systemd fix completed successfully!"
echo "📊 Final status:"
sudo systemctl status crybb-bot --no-pager -l

echo "📋 Recent logs:"
sudo journalctl -u crybb-bot -n 50 --no-pager

echo "🌐 Health check:"
curl -fsS localhost:8000/health | jq .

echo "📊 Metrics:"
curl -fsS localhost:8000/metrics | jq .