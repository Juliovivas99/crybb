# CryBB Bot DigitalOcean Deployment Guide

## 🚀 Complete 24/7 Deployment Setup

This guide will deploy your CryBB Twitter bot to a DigitalOcean droplet with full security hardening, automatic restarts, and monitoring.

### 📋 Prerequisites

- DigitalOcean account
- SSH key pair (public/private)
- Your `.env` file with all API keys
- Your GitHub repository URL

### 🎯 Quick Start (5 minutes)

1. **Create DigitalOcean Droplet:**

   - OS: Ubuntu 22.04 LTS
   - Size: Basic $6/month (1GB RAM, 1 CPU)
   - Add your SSH key
   - Enable monitoring

2. **Deploy from your Mac:**

   ```bash
   cd /Users/juliovivas/Vscode/crybb
   chmod +x scripts/deploy_complete.sh
   ./scripts/deploy_complete.sh YOUR_DROPLET_IP
   ```

3. **That's it!** Your bot is now running 24/7.

---

## 📖 Detailed Step-by-Step Guide

### Step 1: Create DigitalOcean Droplet

1. **Log into DigitalOcean** and create a new droplet
2. **Choose configuration:**

   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic $6/month (sufficient for bot)
   - **Authentication:** SSH Key (add your public key)
   - **Hostname:** `crybb-bot` (optional)
   - **Enable monitoring:** Yes

3. **Create droplet** and note the IP address

### Step 2: Prepare Your Local Environment

1. **Ensure your `.env` file is ready:**

   ```bash
   cd /Users/juliovivas/Vscode/crybb
   ls -la .env  # Should exist and contain your API keys
   ```

2. **Update repository URL in deployment script:**

   ```bash
   nano scripts/deploy_complete.sh
   # Update REPO_URL="https://github.com/YOURUSERNAME/crybb.git"
   ```

3. **Make scripts executable:**
   ```bash
   chmod +x scripts/*.sh
   ```

### Step 3: Deploy the Bot

**Run the complete deployment script:**

```bash
./scripts/deploy_complete.sh YOUR_DROPLET_IP
```

This script will:

- ✅ Create deploy user with sudo privileges
- ✅ Install Python 3.11 and all dependencies
- ✅ Clone your repository to `/opt/crybb-bot`
- ✅ Set up virtual environment
- ✅ Upload and configure your `.env` file
- ✅ Create and enable systemd service
- ✅ Configure firewall (UFW)
- ✅ Set up fail2ban intrusion prevention
- ✅ Start the bot service
- ✅ Verify deployment

### Step 4: Apply Security Hardening (Optional but Recommended)

```bash
# Upload hardening script
scp scripts/harden_complete.sh root@YOUR_DROPLET_IP:/tmp/

# Run hardening on droplet
ssh root@YOUR_DROPLET_IP "chmod +x /tmp/harden_complete.sh && /tmp/harden_complete.sh"
```

### Step 5: Verify Deployment

**SSH into your droplet:**

```bash
ssh root@YOUR_DROPLET_IP
```

**Check service status:**

```bash
systemctl status crybb-bot
```

**View logs:**

```bash
journalctl -u crybb-bot -f
```

**Test health endpoint:**

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

---

## 🔧 Service Management

### Basic Commands

```bash
# Service control
sudo systemctl start crybb-bot      # Start the bot
sudo systemctl stop crybb-bot       # Stop the bot
sudo systemctl restart crybb-bot    # Restart the bot
sudo systemctl status crybb-bot     # Check status

# Enable/disable auto-start
sudo systemctl enable crybb-bot     # Start on boot
sudo systemctl disable crybb-bot    # Don't start on boot
```

### Monitoring and Logs

```bash
# Follow logs in real-time
journalctl -u crybb-bot -f

# View recent logs
journalctl -u crybb-bot --since "1 hour ago"

# View error logs only
journalctl -u crybb-bot -p err

# View logs since specific date
journalctl -u crybb-bot --since "2024-01-01 00:00:00"
```

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed metrics
curl http://localhost:8000/metrics

# Check if service is responding
systemctl is-active crybb-bot
```

---

## 🔒 Security Features

### Firewall (UFW)

- **SSH (port 22):** Allowed
- **Health endpoint (port 8000):** Allowed
- **HTTP/HTTPS (ports 80/443):** Allowed for updates
- **All other ports:** Blocked

### Intrusion Prevention (Fail2ban)

- **SSH protection:** Blocks IPs after 3 failed attempts
- **Ban duration:** 1 hour
- **Monitoring:** `/var/log/auth.log`

### SSH Security

- **Password authentication:** Disabled
- **Key-based authentication:** Required
- **Root login:** Enabled but secured
- **Connection timeout:** 5 minutes

### Automatic Security Updates

- **Security patches:** Installed automatically
- **System updates:** Manual (recommended)
- **Monitoring:** Daily security reports

---

## 🔄 Updates and Maintenance

### Quick Update (Code Changes)

```bash
# SSH into droplet
ssh root@YOUR_DROPLET_IP

# Update code
cd /opt/crybb-bot
git pull

# Restart service
systemctl restart crybb-bot
```

### Environment Changes

```bash
# Upload new .env file
scp .env root@YOUR_DROPLET_IP:/tmp/.env

# On droplet
sudo cp /tmp/.env /opt/crybb-bot/.env
sudo chown root:root /opt/crybb-bot/.env
sudo chmod 600 /opt/crybb-bot/.env
sudo systemctl restart crybb-bot
```

### System Updates

```bash
# Update system packages
apt update && apt upgrade -y

# Restart bot after system updates
systemctl restart crybb-bot
```

---

## 📊 Monitoring and Troubleshooting

### Resource Monitoring

```bash
# Check system resources
htop
df -h
free -h

# Check bot process
ps aux | grep python
```

### Log Analysis

```bash
# Check for errors
journalctl -u crybb-bot -p err --since "1 hour ago"

# Check startup logs
journalctl -u crybb-bot --since "10 minutes ago"

# Check system logs
journalctl -f
```

### Common Issues

**Service won't start:**

```bash
# Check detailed status
systemctl status crybb-bot -l

# Check logs
journalctl -u crybb-bot --since "10 minutes ago"

# Verify .env file
ls -la /opt/crybb-bot/.env
```

**Bot not responding:**

```bash
# Check if service is running
systemctl is-active crybb-bot

# Check recent logs
journalctl -u crybb-bot --since "1 hour ago"

# Test health endpoint
curl -v http://localhost:8000/health
```

**Rate limiting issues:**

```bash
# Check Twitter API logs
journalctl -u crybb-bot | grep -i "rate"

# Check bot configuration
cat /opt/crybb-bot/.env | grep -E "(POLL_SECONDS|RATE_LIMIT)"
```

---

## 🎯 Testing Your Bot

### 1. Health Check

```bash
curl http://YOUR_DROPLET_IP:8000/health
```

### 2. Test Bot Functionality

1. **Mention your bot** on Twitter: `@crybbmaker`
2. **Check logs** for processing: `journalctl -u crybb-bot -f`
3. **Verify response** appears on Twitter

### 3. Monitor Performance

```bash
# Check resource usage
htop

# Check disk space
df -h

# Check memory usage
free -h
```

---

## 🔧 Advanced Configuration

### Custom Polling Interval

Edit `/opt/crybb-bot/.env`:

```bash
POLL_SECONDS=30  # Change from default 15 seconds
```

### Rate Limiting

```bash
RATE_LIMIT_PER_HOUR=10  # Adjust as needed
```

### AI Model Configuration

```bash
REPLICATE_MODEL=google/nano-banana
REPLICATE_TIMEOUT_SECS=120
AI_MAX_CONCURRENCY=2
```

---

## 📈 Scaling and Optimization

### Resource Monitoring

```bash
# Set up monitoring alerts
# Monitor CPU, memory, and disk usage
# Set up log rotation for large log files
```

### Performance Tuning

```bash
# Adjust polling frequency based on usage
# Monitor Twitter API rate limits
# Optimize image processing pipeline
```

### Backup Strategy

```bash
# Backup .env file
sudo cp /opt/crybb-bot/.env /opt/crybb-bot/.env.backup

# Backup outbox directory
sudo tar -czf /opt/crybb-bot-backup-$(date +%Y%m%d).tar.gz /opt/crybb-bot
```

---

## 🎉 Success!

Your CryBB bot is now running 24/7 on DigitalOcean with:

- ✅ **Automatic startup** on boot
- ✅ **Automatic restart** on failure
- ✅ **Security hardening** (firewall, fail2ban, SSH)
- ✅ **Health monitoring** endpoints
- ✅ **Comprehensive logging**
- ✅ **Easy maintenance** and updates

### Quick Reference Commands

```bash
# Service management
sudo systemctl start|stop|restart|status crybb-bot

# Logs
journalctl -u crybb-bot -f

# Health check
curl http://localhost:8000/health

# Security check
sudo crybb-security-check
```

**Your bot is ready to process Twitter mentions 24/7!** 🚀
