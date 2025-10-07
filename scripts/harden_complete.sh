#!/usr/bin/env bash
set -e

# CryBB Bot Security Hardening Script
# This script applies comprehensive security hardening to the DigitalOcean droplet

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root"
    exit 1
fi

log_info "Starting security hardening for CryBB Bot..."

# Update system packages
log_info "Updating system packages..."
apt update && apt upgrade -y

# Install security packages
log_info "Installing security packages..."
apt install -y \
    ufw \
    fail2ban \
    unattended-upgrades \
    apt-listchanges \
    debsums \
    rkhunter \
    chkrootkit \
    logwatch \
    aide

# Configure UFW firewall
log_info "Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (be careful with this!)
ufw allow ssh
ufw allow 22/tcp

# Allow CryBB bot health endpoint
ufw allow 8000/tcp

# Allow HTTP/HTTPS if needed for updates
ufw allow 80/tcp
ufw allow 443/tcp

ufw --force enable
log_success "UFW firewall configured"

# Configure fail2ban
log_info "Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200

[nginx-http-auth]
enabled = false

[nginx-limit-req]
enabled = false
EOF

systemctl enable fail2ban
systemctl restart fail2ban
log_success "Fail2ban configured"

# Configure automatic security updates
log_info "Configuring automatic security updates..."
cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF

systemctl enable unattended-upgrades
systemctl start unattended-upgrades
log_success "Automatic security updates configured"

# Secure SSH configuration
log_info "Hardening SSH configuration..."
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

cat > /etc/ssh/sshd_config << 'EOF'
# SSH Hardening Configuration
Port 22
Protocol 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key

# Logging
SyslogFacility AUTH
LogLevel INFO

# Authentication
LoginGraceTime 60
PermitRootLogin yes
StrictModes yes
MaxAuthTries 3
MaxSessions 10

# Key-based authentication
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys

# Disable password authentication for root
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no
KerberosAuthentication no
GSSAPIAuthentication no

# Disable X11 forwarding
X11Forwarding no
X11DisplayOffset 10
PrintMotd no
PrintLastLog yes
TCPKeepAlive yes

# Security settings
UsePrivilegeSeparation yes
ClientAliveInterval 300
ClientAliveCountMax 2
Compression delayed
AllowUsers root crybb

# Disable unused features
UseDNS no
EOF

systemctl restart ssh
log_success "SSH configuration hardened"

# Set up log monitoring
log_info "Setting up log monitoring..."
cat > /etc/logwatch/conf/logwatch.conf << 'EOF'
LogDir = /var/log
TmpDir = /var/cache/logwatch
MailTo = root
MailFrom = Logwatch
Print = No
Save = /var/log/logwatch
Range = yesterday
Detail = Med
Service = All
Format = text
Encode = none
EOF

# Create log rotation for CryBB bot
cat > /etc/logrotate.d/crybb-bot << 'EOF'
/var/log/crybb-bot.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload crybb-bot > /dev/null 2>&1 || true
    endscript
}
EOF

log_success "Log monitoring configured"

# Set up file integrity monitoring with AIDE
log_info "Setting up file integrity monitoring..."
aide --init
mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
log_success "File integrity monitoring configured"

# Create security monitoring script
log_info "Creating security monitoring script..."
cat > /usr/local/bin/crybb-security-check << 'EOF'
#!/bin/bash
# CryBB Security Check Script

echo "=== CryBB Security Check $(date) ==="

# Check UFW status
echo "UFW Status:"
ufw status

# Check fail2ban status
echo -e "\nFail2ban Status:"
fail2ban-client status sshd

# Check for rootkits
echo -e "\nRootkit Check:"
rkhunter --check --skip-keypress

# Check file integrity
echo -e "\nFile Integrity Check:"
aide --check

# Check system updates
echo -e "\nAvailable Updates:"
apt list --upgradable

echo -e "\n=== Security Check Complete ==="
EOF

chmod +x /usr/local/bin/crybb-security-check

# Create cron job for security checks
cat > /etc/cron.d/crybb-security << 'EOF'
# CryBB Security Monitoring
0 2 * * * root /usr/local/bin/crybb-security-check >> /var/log/crybb-security.log 2>&1
0 3 * * 0 root rkhunter --update
EOF

log_success "Security monitoring configured"

# Set up logwatch for daily security reports
cat > /etc/cron.d/logwatch << 'EOF'
# Logwatch security reports
0 4 * * * root /usr/sbin/logwatch --output mail --mailto root --detail high
EOF

log_success "Daily security reports configured"

# Final security recommendations
log_success "Security hardening completed!"
echo ""
log_info "Security features enabled:"
echo "  ✅ UFW firewall (SSH + port 8000)"
echo "  ✅ Fail2ban intrusion prevention"
echo "  ✅ Automatic security updates"
echo "  ✅ SSH hardening (key-only auth)"
echo "  ✅ File integrity monitoring (AIDE)"
echo "  ✅ Rootkit detection (rkhunter)"
echo "  ✅ Daily security reports (logwatch)"
echo "  ✅ Log rotation and monitoring"
echo ""
log_info "Security monitoring commands:"
echo "  sudo crybb-security-check    # Manual security check"
echo "  sudo fail2ban-client status   # Check fail2ban status"
echo "  sudo ufw status              # Check firewall status"
echo "  sudo aide --check            # Check file integrity"
echo ""
log_warning "Important security notes:"
echo "  - SSH password authentication is disabled"
echo "  - Only key-based authentication is allowed"
echo "  - Root login is enabled but secured"
echo "  - Daily security reports sent to root"
echo "  - Automatic security updates enabled"
echo ""
log_info "To view security logs:"
echo "  tail -f /var/log/crybb-security.log"
echo "  journalctl -u fail2ban -f"
echo "  journalctl -u ssh -f"
