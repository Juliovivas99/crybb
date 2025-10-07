#!/usr/bin/env bash
set -e

# CryBB Bot Complete Deployment Script for DigitalOcean
# This script sets up a complete production environment for the CryBB Twitter bot

# Configuration
DROPLET_IP="${1:-}"
APP_DIR="/opt/crybb-bot"
SERVICE_NAME="crybb-bot"
DEPLOY_USER="crybb"
REPO_URL="https://github.com/YOURUSERNAME/crybb.git"  # Update this with your actual repo URL

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
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

check_requirements() {
    log_info "Checking deployment requirements..."
    
    if [ -z "$DROPLET_IP" ]; then
        log_error "Please provide droplet IP as first argument"
        echo "Usage: $0 <DROPLET_IP>"
        exit 1
    fi
    
    if [ ! -f ".env" ]; then
        log_error ".env file not found in current directory"
        echo "Please ensure your .env file is in the same directory as this script"
        exit 1
    fi
    
    log_success "Requirements check passed"
}

upload_files() {
    log_info "Uploading deployment files to droplet..."
    
    # Upload .env file
    scp .env root@$DROPLET_IP:/tmp/.env
    log_success "Uploaded .env file"
    
    # Upload deployment script
    scp scripts/deploy_complete.sh root@$DROPLET_IP:/tmp/deploy_complete.sh
    log_success "Uploaded deployment script"
    
    # Upload systemd service file
    scp scripts/crybb-bot.service root@$DROPLET_IP:/tmp/crybb-bot.service
    log_success "Uploaded systemd service file"
}

run_deployment() {
    log_info "Starting deployment on droplet $DROPLET_IP..."
    
    ssh root@$DROPLET_IP << 'EOF'
        set -e
        
        # Colors for remote output
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
        
        # Update system packages
        log_info "Updating system packages..."
        apt update && apt upgrade -y
        
        # Install essential packages
        log_info "Installing essential packages..."
        apt install -y \
            python3.11 \
            python3.11-venv \
            python3.11-dev \
            python3-pip \
            git \
            curl \
            wget \
            build-essential \
            software-properties-common \
            apt-transport-https \
            ca-certificates \
            gnupg \
            lsb-release \
            unzip \
            htop \
            nano \
            vim \
            ufw \
            fail2ban \
            logrotate
        
        # Install image processing dependencies
        log_info "Installing image processing dependencies..."
        apt install -y \
            libjpeg-dev \
            zlib1g-dev \
            libfreetype6-dev \
            liblcms2-dev \
            libwebp-dev \
            libharfbuzz-dev \
            libfribidi-dev \
            libxcb1-dev \
            libtiff5-dev \
            libopenjp2-7-dev
        
        # Create deploy user with sudo privileges
        log_info "Creating deploy user..."
        if ! id "$DEPLOY_USER" &>/dev/null; then
            useradd -m -s /bin/bash $DEPLOY_USER
            usermod -aG sudo $DEPLOY_USER
            mkdir -p /home/$DEPLOY_USER/.ssh
            chmod 700 /home/$DEPLOY_USER/.ssh
            
            # Copy root's SSH key to deploy user
            if [ -f /root/.ssh/authorized_keys ]; then
                cp /root/.ssh/authorized_keys /home/$DEPLOY_USER/.ssh/
                chown -R $DEPLOY_USER:$DEPLOY_USER /home/$DEPLOY_USER/.ssh
                chmod 600 /home/$DEPLOY_USER/.ssh/authorized_keys
            fi
            
            log_success "Created deploy user: $DEPLOY_USER"
        else
            log_warning "Deploy user $DEPLOY_USER already exists"
        fi
        
        # Configure firewall
        log_info "Configuring firewall..."
        ufw --force reset
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 8000/tcp  # Health endpoint
        ufw --force enable
        log_success "Firewall configured"
        
        # Configure fail2ban
        log_info "Configuring fail2ban..."
        cat > /etc/fail2ban/jail.local << 'FAIL2BAN_EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
FAIL2BAN_EOF
        
        systemctl enable fail2ban
        systemctl start fail2ban
        log_success "Fail2ban configured"
        
        # Clone repository
        log_info "Setting up repository..."
        if [ ! -d "$APP_DIR" ]; then
            git clone $REPO_URL $APP_DIR
            chown -R root:root $APP_DIR
            log_success "Repository cloned to $APP_DIR"
        else
            log_warning "Repository already exists at $APP_DIR"
            cd $APP_DIR
            git pull
            log_success "Repository updated"
        fi
        
        # Set up Python virtual environment
        log_info "Setting up Python virtual environment..."
        cd $APP_DIR
        python3.11 -m venv venv
        
        # Upgrade pip and install dependencies
        log_info "Installing Python dependencies..."
        ./venv/bin/pip install --upgrade pip
        ./venv/bin/pip install -r requirements.txt
        
        # Copy environment file
        log_info "Setting up environment configuration..."
        if [ -f /tmp/.env ]; then
            cp /tmp/.env $APP_DIR/.env
            chown root:root $APP_DIR/.env
            chmod 600 $APP_DIR/.env
            log_success "Environment file configured"
        else
            log_error "No .env file found in /tmp/"
            exit 1
        fi
        
        # Create systemd service
        log_info "Setting up systemd service..."
        cp /tmp/crybb-bot.service /etc/systemd/system/$SERVICE_NAME.service
        
        # Reload systemd and enable service
        log_info "Enabling and starting service..."
        systemctl daemon-reload
        systemctl enable $SERVICE_NAME.service
        
        # Set proper permissions
        chown -R root:root $APP_DIR
        chmod +x $APP_DIR/venv/bin/python3
        
        log_success "Deployment completed successfully!"
        
        # Show service status
        log_info "Service status:"
        systemctl status $SERVICE_NAME.service --no-pager || true
        
        # Show useful commands
        echo ""
        log_info "Useful commands:"
        echo "  Check logs:     journalctl -u $SERVICE_NAME -f"
        echo "  Restart bot:    systemctl restart $SERVICE_NAME"
        echo "  Stop bot:       systemctl stop $SERVICE_NAME"
        echo "  Check status:   systemctl status $SERVICE_NAME"
        echo "  Health check:   curl http://localhost:8000/health"
        echo "  Metrics:        curl http://localhost:8000/metrics"
        
EOF
}

start_service() {
    log_info "Starting CryBB bot service..."
    
    ssh root@$DROPLET_IP << 'EOF'
        systemctl start crybb-bot.service
        sleep 5
        
        if systemctl is-active --quiet crybb-bot.service; then
            echo -e "\033[0;32m[SUCCESS]\033[0m CryBB bot service is running!"
        else
            echo -e "\033[0;31m[ERROR]\033[0m CryBB bot service failed to start"
            systemctl status crybb-bot.service --no-pager
            exit 1
        fi
EOF
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    if curl -s -f "http://$DROPLET_IP:8000/health" > /dev/null; then
        log_success "Health endpoint is responding"
    else
        log_warning "Health endpoint not responding (this might be expected if firewall blocks external access)"
    fi
    
    # Test metrics endpoint
    log_info "Testing metrics endpoint..."
    if curl -s -f "http://$DROPLET_IP:8000/metrics" > /dev/null; then
        log_success "Metrics endpoint is responding"
    else
        log_warning "Metrics endpoint not responding"
    fi
    
    # Check service status
    log_info "Checking service status..."
    ssh root@$DROPLET_IP "systemctl is-active crybb-bot.service" && log_success "Service is active" || log_error "Service is not active"
}

show_final_instructions() {
    echo ""
    log_success "🎉 Deployment Complete!"
    echo ""
    echo "Your CryBB bot is now running on DigitalOcean!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. SSH into your droplet:"
    echo "   ssh root@$DROPLET_IP"
    echo ""
    echo "2. Monitor the bot:"
    echo "   journalctl -u crybb-bot -f"
    echo ""
    echo "3. Check health status:"
    echo "   curl http://localhost:8000/health"
    echo ""
    echo "4. Test the bot by mentioning @crybbmaker on Twitter"
    echo ""
    echo "🔧 Service Management:"
    echo "   sudo systemctl start crybb-bot     # Start"
    echo "   sudo systemctl stop crybb-bot      # Stop"
    echo "   sudo systemctl restart crybb-bot   # Restart"
    echo "   sudo systemctl status crybb-bot    # Status"
    echo ""
    echo "📊 Monitoring:"
    echo "   journalctl -u crybb-bot -f         # Follow logs"
    echo "   curl http://localhost:8000/health  # Health check"
    echo "   curl http://localhost:8000/metrics # Detailed metrics"
    echo ""
    echo "🔒 Security:"
    echo "   - UFW firewall enabled (SSH + port 8000)"
    echo "   - Fail2ban intrusion prevention active"
    echo "   - Deploy user '$DEPLOY_USER' created with sudo access"
    echo ""
    echo "🚀 Your bot will automatically start on boot and restart on failure!"
}

# Main execution
main() {
    echo "🚀 CryBB Bot DigitalOcean Deployment Script"
    echo "=============================================="
    echo ""
    
    check_requirements
    upload_files
    run_deployment
    start_service
    verify_deployment
    show_final_instructions
}

# Run main function
main "$@"
