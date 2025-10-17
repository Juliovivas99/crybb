#!/bin/bash
# CryBB Bot Debug and Fix Script for DigitalOcean Droplet
# Run this script to diagnose and fix startup issues

set -e

echo "=== CryBB Bot Debug and Fix Script ==="
echo "Target: DigitalOcean droplet at 64.225.24.163"
echo "Date: $(date)"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root: sudo $0"
    exit 1
fi

# Set working directory
cd /opt/crybb-bot
log_info "Working directory: $(pwd)"

# Step 1: Check current service status
log_info "=== Checking Current Service Status ==="
systemctl status crybb-bot --no-pager || true
echo

# Step 2: Check recent logs
log_info "=== Checking Recent Logs ==="
journalctl -u crybb-bot --no-pager -n 50 || true
echo

# Step 3: Stop the service for debugging
log_info "=== Stopping Service for Debugging ==="
systemctl stop crybb-bot || true
sleep 2

# Step 4: Check environment file
log_info "=== Checking Environment Configuration ==="
if [ -f ".env" ]; then
    log_info ".env file exists"
    # Check if .env has required variables (without showing values)
    required_vars=("CLIENT_ID" "CLIENT_SECRET" "API_KEY" "API_SECRET" "ACCESS_TOKEN" "ACCESS_SECRET" "BEARER_TOKEN")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        log_info "All required environment variables present in .env"
    else
        log_error "Missing environment variables: ${missing_vars[*]}"
        log_error "Please check your .env file"
        exit 1
    fi
else
    log_error ".env file missing!"
    exit 1
fi

# Step 5: Check Python environment
log_info "=== Checking Python Environment ==="
if [ -d "venv" ]; then
    log_info "Virtual environment exists"
    if [ -f "venv/bin/python3" ]; then
        log_info "Python executable found: $(venv/bin/python3 --version)"
    else
        log_error "Python executable missing in venv"
        exit 1
    fi
else
    log_error "Virtual environment missing!"
    exit 1
fi

# Step 6: Check dependencies
log_info "=== Checking Python Dependencies ==="
venv/bin/pip list | grep -E "(requests|fastapi|uvicorn|Pillow|python-dotenv)" || {
    log_warn "Some dependencies may be missing. Installing..."
    venv/bin/pip install -r requirements.txt
}

# Step 7: Run debug script
log_info "=== Running Debug Script ==="
if [ -f "debug_startup.py" ]; then
    PYTHONPATH=/opt/crybb-bot venv/bin/python3 debug_startup.py
    debug_exit_code=$?
    
    if [ $debug_exit_code -eq 0 ]; then
        log_info "Debug script passed - all components working"
    else
        log_error "Debug script failed - see output above"
        log_error "Bot may have configuration or dependency issues"
    fi
else
    log_warn "Debug script not found, skipping debug test"
fi

# Step 8: Test manual execution
log_info "=== Testing Manual Bot Execution ==="
log_info "Running bot manually for 10 seconds to check initialization..."

# Create a timeout wrapper
timeout 10s bash -c '
    cd /opt/crybb-bot
    export PYTHONPATH=/opt/crybb-bot
    export PYTHONUNBUFFERED=1
    venv/bin/python3 -m src.main
' 2>&1 | head -20 || {
    log_warn "Manual execution timed out or failed"
    log_info "This is expected - bot runs indefinitely"
}

# Step 9: Check systemd service file
log_info "=== Checking Systemd Service Configuration ==="
if [ -f "/etc/systemd/system/crybb-bot.service" ]; then
    log_info "Service file exists"
    
    # Check for common issues
    if grep -q "WorkingDirectory=/opt/crybb-bot" /etc/systemd/system/crybb-bot.service; then
        log_info "✓ WorkingDirectory correctly set"
    else
        log_warn "WorkingDirectory may be incorrect"
    fi
    
    if grep -q "Environment=PYTHONPATH=/opt/crybb-bot" /etc/systemd/system/crybb-bot.service; then
        log_info "✓ PYTHONPATH correctly set"
    else
        log_warn "PYTHONPATH may be missing"
    fi
    
    if grep -q "EnvironmentFile=/opt/crybb-bot/.env" /etc/systemd/system/crybb-bot.service; then
        log_info "✓ EnvironmentFile correctly set"
    else
        log_warn "EnvironmentFile may be missing"
    fi
else
    log_error "Service file missing at /etc/systemd/system/crybb-bot.service"
fi

# Step 10: Reload systemd and restart service
log_info "=== Reloading Systemd and Restarting Service ==="
systemctl daemon-reload
sleep 2

log_info "Starting crybb-bot service..."
systemctl start crybb-bot
sleep 5

# Step 11: Check service status
log_info "=== Checking Service Status After Restart ==="
systemctl status crybb-bot --no-pager || true

# Step 12: Check health endpoint
log_info "=== Checking Health Endpoint ==="
sleep 5  # Give the service time to start
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    log_info "✓ Health endpoint responding"
    curl -s http://localhost:8000/health | python3 -m json.tool || true
else
    log_warn "Health endpoint not responding"
fi

# Step 13: Monitor logs for a few seconds
log_info "=== Monitoring Recent Logs ==="
timeout 10s journalctl -u crybb-bot -f --no-pager || true

echo
log_info "=== Debug and Fix Complete ==="
log_info "Service status: $(systemctl is-active crybb-bot)"
log_info "Health check: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health 2>/dev/null || echo 'failed')"

echo
log_info "Next steps:"
log_info "1. Monitor logs: journalctl -u crybb-bot -f"
log_info "2. Check health: curl http://localhost:8000/health"
log_info "3. Check metrics: curl http://localhost:8000/metrics"
log_info "4. If issues persist, run: python3 debug_startup.py"



