# CryBB Bot Startup Debug Guide

## Problem

The CryBB bot service shows "active (running)" but no actual bot activity in logs. Missing initialization messages like "Twitter API v2 client initialized", "Bot initialized", etc.

## Root Cause Analysis

Based on the code examination, the most likely causes are:

1. **Silent Import Failures**: Missing dependencies or Python path issues
2. **Configuration Validation Failures**: Missing environment variables causing silent exits
3. **Twitter API Authentication Issues**: Invalid credentials preventing bot identity resolution
4. **Systemd Environment Issues**: Environment variables not properly loaded

## Debugging Steps

### Step 1: Run the Debug Script

```bash
# SSH to your DigitalOcean droplet
ssh root@64.225.24.163

# Navigate to bot directory
cd /opt/crybb-bot

# Run the comprehensive debug script
sudo ./scripts/debug_and_fix.sh
```

### Step 2: Manual Testing (if debug script fails)

```bash
# Test Python imports
cd /opt/crybb-bot
PYTHONPATH=/opt/crybb-bot /opt/crybb-bot/venv/bin/python3 debug_startup.py

# Test manual bot execution
cd /opt/crybb-bot
PYTHONPATH=/opt/crybb-bot /opt/crybb-bot/venv/bin/python3 -m src.main
```

### Step 3: Check Specific Issues

#### Environment Variables

```bash
# Check if .env file exists and has required variables
cd /opt/crybb-bot
cat .env | grep -E "(CLIENT_ID|CLIENT_SECRET|API_KEY|API_SECRET|ACCESS_TOKEN|ACCESS_SECRET|BEARER_TOKEN)"
```

#### Python Dependencies

```bash
# Check installed packages
cd /opt/crybb-bot
venv/bin/pip list

# Reinstall if needed
venv/bin/pip install -r requirements.txt
```

#### Systemd Service

```bash
# Check service configuration
systemctl cat crybb-bot

# Check service logs
journalctl -u crybb-bot -f
```

## Expected Bot Initialization Sequence

When working correctly, you should see these messages in order:

1. `Twitter API v2 client initialized (Bearer reads, OAuth1a writes)`
2. `Bot initialized: @crybbmaker (ID: 123456789)`
3. `Starting CryBB Maker Bot...`
4. `Health server started on port 8000`
5. `Polling for mentions since ID: None`

## Common Fixes

### Fix 1: Missing Dependencies

```bash
cd /opt/crybb-bot
venv/bin/pip install -r requirements.txt
```

### Fix 2: Environment Variables

```bash
# Ensure .env file exists with all required variables
cd /opt/crybb-bot
nano .env
# Add missing variables:
# CLIENT_ID=your_client_id
# CLIENT_SECRET=your_client_secret
# API_KEY=your_api_key
# API_SECRET=your_api_secret
# ACCESS_TOKEN=your_access_token
# ACCESS_SECRET=your_access_secret
# BEARER_TOKEN=your_bearer_token
```

### Fix 3: Systemd Service Reload

```bash
systemctl daemon-reload
systemctl restart crybb-bot
```

### Fix 4: Python Path Issues

```bash
# Ensure PYTHONPATH is set correctly
export PYTHONPATH=/opt/crybb-bot
systemctl restart crybb-bot
```

## Verification

After fixes, verify the bot is working:

1. **Service Status**: `systemctl status crybb-bot`
2. **Health Endpoint**: `curl http://localhost:8000/health`
3. **Logs**: `journalctl -u crybb-bot -f`
4. **Metrics**: `curl http://localhost:8000/metrics`

## Files Created for Debugging

- `debug_startup.py`: Comprehensive Python debug script
- `scripts/debug_and_fix.sh`: Automated bash script for diagnosis and fixes

## Next Steps

1. Run the debug script on your droplet
2. Fix any issues identified
3. Monitor logs to ensure bot is polling for mentions
4. Test with a mention to verify end-to-end functionality



