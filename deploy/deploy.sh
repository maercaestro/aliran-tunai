#!/bin/bash

# AliranTunai Deployment Script
# This script deploys the application to EC2 with proper setup

set -e  # Exit on any error

# Configuration
APP_DIR="/opt/aliran-tunai"
APP_USER="ubuntu"
PYTHON_VERSION="3.12"
SERVICE_NAME="aliran-tunai"
WHATSAPP_SERVICE_NAME="aliran-whatsapp"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root for system operations
check_sudo() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root directly. Use sudo when needed."
        exit 1
    fi
}

# Install system dependencies
install_system_dependencies() {
    log "Installing system dependencies..."
    
    sudo apt update
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        nginx \
        git \
        curl \
        wget \
        unzip \
        supervisor \
        tesseract-ocr \
        tesseract-ocr-eng \
        certbot \
        python3-certbot-nginx
    
    success "System dependencies installed successfully"
}

# Setup application directory
setup_app_directory() {
    log "Setting up application directory..."
    
    sudo mkdir -p $APP_DIR/{current,backup,releases}
    sudo mkdir -p /var/log/aliran-tunai
    sudo chown -R $APP_USER:$APP_USER $APP_DIR
    sudo chown -R $APP_USER:$APP_USER /var/log/aliran-tunai
    
    success "Application directory setup completed"
}

# Setup Python environment
setup_python_environment() {
    log "Setting up Python virtual environment..."
    
    cd $APP_DIR/current
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log "Virtual environment created"
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    success "Python environment setup completed"
}

# Setup systemd services
setup_services() {
    log "Setting up systemd services..."
    
    # Copy service files
    sudo cp deploy/aliran-tunai.service /etc/systemd/system/
    sudo cp deploy/aliran-whatsapp.service /etc/systemd/system/
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable services
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl enable $WHATSAPP_SERVICE_NAME
    
    success "Systemd services setup completed"
}

# Setup nginx
setup_nginx() {
    log "Setting up nginx configuration..."
    
    # Copy nginx configuration
    sudo cp deploy/nginx.conf /etc/nginx/sites-available/aliran-tunai
    
    # Create symlink if it doesn't exist
    if [ ! -L /etc/nginx/sites-enabled/aliran-tunai ]; then
        sudo ln -s /etc/nginx/sites-available/aliran-tunai /etc/nginx/sites-enabled/
    fi
    
    # Test nginx configuration
    sudo nginx -t
    
    # Reload nginx
    sudo systemctl reload nginx
    
    success "Nginx configuration setup completed"
}

# Setup SSL certificate
setup_ssl() {
    read -p "Enter your domain name (leave empty to skip SSL setup): " DOMAIN
    
    if [ -n "$DOMAIN" ]; then
        log "Setting up SSL certificate for $DOMAIN..."
        
        # Update nginx configuration with actual domain
        sudo sed -i "s/your-domain.com/$DOMAIN/g" /etc/nginx/sites-available/aliran-tunai
        sudo nginx -t && sudo systemctl reload nginx
        
        # Obtain SSL certificate
        sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN || warning "SSL setup failed - you may need to configure it manually"
        
        success "SSL certificate setup completed for $DOMAIN"
    else
        warning "SSL setup skipped - remember to configure it manually for production"
    fi
}

# Create environment file
create_env_file() {
    log "Creating environment configuration file..."
    
    if [ ! -f "$APP_DIR/current/.env" ]; then
        cat > $APP_DIR/current/.env << EOF
# Database Configuration
MONGO_URI=your_mongodb_connection_string

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# WhatsApp Business API Configuration
WHATSAPP_VERIFY_TOKEN=your_whatsapp_verify_token
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/aliran-tunai/app.log
EOF
        
        warning "Environment file created at $APP_DIR/current/.env"
        warning "Please update the environment variables with your actual values!"
    else
        log "Environment file already exists"
    fi
}

# Start services
start_services() {
    log "Starting application services..."
    
    # Stop services if running
    sudo systemctl stop $WHATSAPP_SERVICE_NAME || true
    sudo systemctl stop $SERVICE_NAME || true
    
    # Start services
    sudo systemctl start $SERVICE_NAME
    sudo systemctl start $WHATSAPP_SERVICE_NAME
    
    # Check service status
    sleep 5
    
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        success "Telegram bot service started successfully"
    else
        error "Failed to start Telegram bot service"
        sudo systemctl status $SERVICE_NAME
        return 1
    fi
    
    if sudo systemctl is-active --quiet $WHATSAPP_SERVICE_NAME; then
        success "WhatsApp API service started successfully"
    else
        error "Failed to start WhatsApp API service"
        sudo systemctl status $WHATSAPP_SERVICE_NAME
        return 1
    fi
}

# Health check
perform_health_check() {
    log "Performing health check..."
    
    # Check if services are running
    if ! sudo systemctl is-active --quiet $SERVICE_NAME; then
        error "Telegram bot service is not running"
        return 1
    fi
    
    if ! sudo systemctl is-active --quiet $WHATSAPP_SERVICE_NAME; then
        error "WhatsApp API service is not running"
        return 1
    fi
    
    # Check if API is responding
    sleep 10  # Give services time to start
    
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        success "API health check passed"
    else
        warning "API health check failed - service may still be starting"
    fi
    
    success "Health check completed"
}

# Setup monitoring (basic)
setup_monitoring() {
    log "Setting up basic monitoring..."
    
    # Create log rotation configuration
    sudo tee /etc/logrotate.d/aliran-tunai > /dev/null << EOF
/var/log/aliran-tunai/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload aliran-tunai
        systemctl reload aliran-whatsapp
    endscript
}
EOF
    
    # Create simple monitoring script
    sudo tee /usr/local/bin/aliran-monitor.sh > /dev/null << 'EOF'
#!/bin/bash

# Simple monitoring script for AliranTunai services
SERVICES=("aliran-tunai" "aliran-whatsapp")
LOG_FILE="/var/log/aliran-tunai/monitor.log"

for service in "${SERVICES[@]}"; do
    if ! systemctl is-active --quiet "$service"; then
        echo "$(date): $service is down, attempting restart" >> "$LOG_FILE"
        systemctl restart "$service"
    fi
done

# Check API endpoint
if ! curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "$(date): API health check failed" >> "$LOG_FILE"
fi
EOF
    
    sudo chmod +x /usr/local/bin/aliran-monitor.sh
    
    # Add to crontab for ubuntu user
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/aliran-monitor.sh") | crontab -
    
    success "Basic monitoring setup completed"
}

# Main deployment function
main() {
    log "Starting AliranTunai deployment..."
    
    check_sudo
    
    # Check if we're in the right directory
    if [ ! -f "requirements.txt" ]; then
        error "requirements.txt not found. Please run this script from the application root directory."
        exit 1
    fi
    
    install_system_dependencies
    setup_app_directory
    
    # Copy application files to deployment directory
    log "Copying application files..."
    sudo cp -r . $APP_DIR/current/
    sudo chown -R $APP_USER:$APP_USER $APP_DIR/current
    
    setup_python_environment
    create_env_file
    setup_services
    setup_nginx
    setup_ssl
    setup_monitoring
    start_services
    perform_health_check
    
    success "Deployment completed successfully!"
    
    log "Next steps:"
    echo "1. Update environment variables in $APP_DIR/current/.env"
    echo "2. Configure your domain DNS to point to this server"
    echo "3. Set up proper SSL certificate if not done already"
    echo "4. Configure MongoDB connection"
    echo "5. Configure Telegram bot webhook"
    echo "6. Configure WhatsApp Business API webhook"
    
    log "Service management commands:"
    echo "- Check status: sudo systemctl status aliran-tunai aliran-whatsapp"
    echo "- View logs: sudo journalctl -u aliran-tunai -f"
    echo "- Restart services: sudo systemctl restart aliran-tunai aliran-whatsapp"
}

# Run main function
main "$@"