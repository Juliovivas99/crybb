# DigitalOcean Droplet Deployment Guide

## ✅ Migration Complete!

Your CryBB bot has been successfully migrated from Docker to a lean Python runtime optimized for DigitalOcean droplets.

### 🗑️ **Removed Docker Components**

- ✅ Deleted `docker-compose.yml`
- ✅ Deleted `Dockerfile`
- ✅ Removed Docker references from README.md
- ✅ Updated Makefile to remove Docker commands

### 🚀 **New Deployment Infrastructure**

- ✅ Created `scripts/deploy.sh` - Complete droplet setup automation
- ✅ Created `scripts/update.sh` - Quick update automation
- ✅ Created `scripts/harden.sh` - Security hardening automation
- ✅ Updated README.md with comprehensive DigitalOcean deployment guide

## 🎯 **Quick Start Deployment**

### 1. Create DigitalOcean Droplet

1. **Create droplet:**

   - OS: Ubuntu 22.04 LTS
   - Size: Basic $6/month (sufficient for bot)
   - Add your SSH key
   - Enable monitoring

2. **Get droplet IP and connect:**
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

### 2. Deploy Bot

1. **Clone repository:**

   ```bash
   git clone https://github.com/YOURUSERNAME/crybb-bot.git /opt/crybb-bot
   ```

2. **Run deployment script:**

   ```bash
   cd /opt/crybb-bot
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh
   ```

3. **Upload environment file:**

   ```bash
   # From your local machine
   scp .env root@YOUR_DROPLET_IP:/tmp/.env

   # On droplet
   sudo cp /tmp/.env /opt/crybb-bot/.env
   sudo chown root:root /opt/crybb-bot/.env
   sudo chmod 600 /opt/crybb-bot/.env
   ```

4. **Run security hardening:**
   ```bash
   chmod +x scripts/harden.sh
   ./scripts/harden.sh
   ```

### 3. Verify Deployment

```bash
# Check service status
sudo systemctl status crybb-bot

# View logs
journalctl -u crybb-bot -f

# Test health endpoint
curl http://localhost:8000/health
```

## 🔧 **Service Management**

The bot runs as a systemd service with automatic restart:

```bash
# Service control
sudo systemctl start crybb-bot      # Start
sudo systemctl stop crybb-bot       # Stop
sudo systemctl restart crybb-bot    # Restart
sudo systemctl status crybb-bot     # Status

# Logs
journalctl -u crybb-bot -f          # Follow logs
journalctl -u crybb-bot --since "1 hour ago"  # Recent logs

# Enable/disable auto-start
sudo systemctl enable crybb-bot     # Start on boot
sudo systemctl disable crybb-bot    # Don't start on boot
```

## 🔄 **Updates**

### Quick Update

```bash
cd /opt/crybb-bot
chmod +x scripts/update.sh
./scripts/update.sh
```

### Manual Update

```bash
cd /opt/crybb-bot
sudo git pull
sudo systemctl restart crybb-bot
```

## 🔒 **Security Features**

The deployment includes comprehensive security hardening:

- **Firewall:** UFW enabled (SSH, HTTP, HTTPS only)
- **SSH Security:** Password auth disabled, key-only access
- **Fail2ban:** Intrusion prevention
- **File Permissions:** .env secured with 600 permissions
- **Log Rotation:** Automatic log management

## 📊 **Monitoring**

### Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Detailed metrics
curl http://localhost:8000/metrics
```

### Log Monitoring

```bash
# Real-time logs
journalctl -u crybb-bot -f

# Error logs only
journalctl -u crybb-bot -p err

# Logs since specific time
journalctl -u crybb-bot --since "2024-01-01 00:00:00"
```

## 🎯 **Acceptance Criteria Met**

- ✅ **Droplet runs bot automatically on boot**
- ✅ **SSH access with log monitoring:** `journalctl -u crybb-bot -f`
- ✅ **Secure .env storage:** 600 permissions, root ownership
- ✅ **24/7 operation:** No dependency on local machine
- ✅ **Docker completely removed:** All Docker files deleted

## 🚨 **Troubleshooting**

### Service Won't Start

```bash
# Check detailed status
sudo systemctl status crybb-bot -l

# Check logs for errors
journalctl -u crybb-bot --since "10 minutes ago"

# Verify .env file
ls -la /opt/crybb-bot/.env
cat /opt/crybb-bot/.env | head -5
```

### Bot Not Responding

```bash
# Check if service is running
sudo systemctl is-active crybb-bot

# Check recent logs
journalctl -u crybb-bot --since "1 hour ago"

# Test health endpoint
curl -v http://localhost:8000/health
```

### Update Issues

```bash
# Check git status
cd /opt/crybb-bot
sudo git status

# Force pull if needed
sudo git fetch --all
sudo git reset --hard origin/main
sudo systemctl restart crybb-bot
```

## 💡 **Pro Tips**

1. **Monitor resource usage:**

   ```bash
   htop
   df -h
   free -h
   ```

2. **Set up log monitoring:**

   ```bash
   # Create log monitoring alias
   echo 'alias botlogs="journalctl -u crybb-bot -f"' >> ~/.bashrc
   ```

3. **Backup .env file:**

   ```bash
   sudo cp /opt/crybb-bot/.env /opt/crybb-bot/.env.backup
   ```

4. **Test bot functionality:**

   ```bash
   # Test health endpoint
   curl http://localhost:8000/health | jq

   # Test AI pipeline
   cd /opt/crybb-bot
   sudo -E venv/bin/python3 tools/run_ai_smoke.py --pfp-url "https://pbs.twimg.com/profile_images/..."
   ```

Your bot is now running as a lean, secure, and maintainable service on DigitalOcean! 🎉
