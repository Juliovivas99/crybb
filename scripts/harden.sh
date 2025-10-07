#!/usr/bin/env bash
set -e

echo "🔒 Hardening DigitalOcean Droplet for CryBB Bot..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install UFW firewall
echo "🔥 Setting up firewall..."
sudo ufw --force enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (for health checks)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw status

# Secure SSH configuration
echo "🔐 Securing SSH..."
sudo tee -a /etc/ssh/sshd_config > /dev/null <<EOF

# CryBB Bot Security Hardening
PasswordAuthentication no
PermitRootLogin prohibit-password
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
EOF

# Restart SSH service
sudo systemctl restart ssh

# Set up fail2ban for additional security
echo "🛡️ Installing fail2ban..."
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Secure .env file permissions
echo "🔐 Securing environment file..."
if [ -f /opt/crybb-bot/.env ]; then
    sudo chown root:root /opt/crybb-bot/.env
    sudo chmod 600 /opt/crybb-bot/.env
    echo "✅ .env file secured with 600 permissions"
else
    echo "⚠️ .env file not found at /opt/crybb-bot/.env"
fi

# Create log rotation for bot logs
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/crybb-bot > /dev/null <<EOF
/var/log/syslog {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload rsyslog > /dev/null 2>&1 || true
    endscript
}
EOF

echo "✅ Security hardening complete!"
echo ""
echo "Security measures applied:"
echo "  🔥 UFW firewall enabled (SSH, HTTP, HTTPS allowed)"
echo "  🔐 SSH password authentication disabled"
echo "  🛡️ Fail2ban installed for intrusion prevention"
echo "  📝 Log rotation configured"
echo "  🔒 .env file secured with 600 permissions"
echo ""
echo "⚠️ Important: Ensure you have SSH key access before disconnecting!"
echo "Test SSH access: ssh root@YOUR_DROPLET_IP"
