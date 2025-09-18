#!/bin/bash

# AliranTunai Monitoring Script
# This script sets up comprehensive monitoring for the application

set -e

# Configuration
MONITOR_DIR="/opt/aliran-tunai/monitoring"
LOG_DIR="/var/log/aliran-tunai"
HEALTH_CHECK_INTERVAL=300  # 5 minutes
ALERT_EMAIL=""  # Set this to your email for alerts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Setup monitoring directories
setup_directories() {
    log "Setting up monitoring directories..."
    
    sudo mkdir -p $MONITOR_DIR
    sudo mkdir -p $LOG_DIR
    sudo mkdir -p /etc/aliran-tunai
    
    sudo chown -R ubuntu:ubuntu $MONITOR_DIR
    sudo chown -R ubuntu:ubuntu $LOG_DIR
    
    success "Monitoring directories created"
}

# Create monitoring configuration
create_monitoring_config() {
    log "Creating monitoring configuration..."
    
    cat > /tmp/monitoring.conf << EOF
# AliranTunai Monitoring Configuration

# Health Check Settings
HEALTH_CHECK_INTERVAL=$HEALTH_CHECK_INTERVAL
HEALTH_CHECK_TIMEOUT=30
HEALTH_CHECK_RETRIES=3

# Alert Settings
ALERT_EMAIL=$ALERT_EMAIL
ALERT_ON_SERVICE_DOWN=true
ALERT_ON_API_FAILURE=true
ALERT_ON_DB_FAILURE=true
ALERT_ON_HIGH_RESOURCE_USAGE=true

# Resource Thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90

# Log Settings
MAX_LOG_SIZE=100M
LOG_RETENTION_DAYS=30
ERROR_THRESHOLD_PER_HOUR=50

# Service Settings
SERVICES=("aliran-tunai" "aliran-whatsapp")
API_ENDPOINTS=("/health" "/whatsapp/webhook")

# External Dependencies
EXTERNAL_SERVICES=("api.openai.com" "api.telegram.org" "graph.facebook.com")
EOF
    
    sudo mv /tmp/monitoring.conf /etc/aliran-tunai/monitoring.conf
    success "Monitoring configuration created"
}

# Create health check service
create_health_check_service() {
    log "Creating health check service..."
    
    cat > /tmp/aliran-health-check.service << EOF
[Unit]
Description=AliranTunai Health Check Service
After=network.target

[Service]
Type=oneshot
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/aliran-tunai/current
Environment=PATH=/opt/aliran-tunai/current/venv/bin
ExecStart=/opt/aliran-tunai/current/venv/bin/python /opt/aliran-tunai/current/scripts/health_check.py --json
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aliran-health-check

[Install]
WantedBy=multi-user.target
EOF
    
    sudo mv /tmp/aliran-health-check.service /etc/systemd/system/
    
    # Create timer for periodic health checks
    cat > /tmp/aliran-health-check.timer << EOF
[Unit]
Description=Run AliranTunai Health Check every 5 minutes
Requires=aliran-health-check.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
Unit=aliran-health-check.service

[Install]
WantedBy=timers.target
EOF
    
    sudo mv /tmp/aliran-health-check.timer /etc/systemd/system/
    
    # Enable and start the timer
    sudo systemctl daemon-reload
    sudo systemctl enable aliran-health-check.timer
    sudo systemctl start aliran-health-check.timer
    
    success "Health check service created and started"
}

# Create resource monitoring script
create_resource_monitor() {
    log "Creating resource monitoring script..."
    
    cat > /tmp/resource_monitor.sh << 'EOF'
#!/bin/bash

# Resource monitoring for AliranTunai
CONFIG_FILE="/etc/aliran-tunai/monitoring.conf"
LOG_FILE="/var/log/aliran-tunai/resource_monitor.log"

# Source configuration
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    CPU_THRESHOLD=80
    MEMORY_THRESHOLD=85
    DISK_THRESHOLD=90
fi

# Function to log with timestamp
log_with_timestamp() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

# Check CPU usage
check_cpu() {
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    CPU_USAGE=${CPU_USAGE%.*}  # Remove decimal part
    
    if [ "$CPU_USAGE" -gt "$CPU_THRESHOLD" ]; then
        log_with_timestamp "HIGH CPU USAGE: ${CPU_USAGE}% (threshold: ${CPU_THRESHOLD}%)"
        return 1
    fi
    return 0
}

# Check memory usage
check_memory() {
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", ($3/$2) * 100.0}')
    
    if [ "$MEMORY_USAGE" -gt "$MEMORY_THRESHOLD" ]; then
        log_with_timestamp "HIGH MEMORY USAGE: ${MEMORY_USAGE}% (threshold: ${MEMORY_THRESHOLD}%)"
        return 1
    fi
    return 0
}

# Check disk usage
check_disk() {
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$DISK_USAGE" -gt "$DISK_THRESHOLD" ]; then
        log_with_timestamp "HIGH DISK USAGE: ${DISK_USAGE}% (threshold: ${DISK_THRESHOLD}%)"
        return 1
    fi
    return 0
}

# Main monitoring function
main() {
    ALERTS=0
    
    if ! check_cpu; then
        ALERTS=$((ALERTS + 1))
    fi
    
    if ! check_memory; then
        ALERTS=$((ALERTS + 1))
    fi
    
    if ! check_disk; then
        ALERTS=$((ALERTS + 1))
    fi
    
    if [ $ALERTS -gt 0 ]; then
        log_with_timestamp "RESOURCE MONITORING: $ALERTS alerts generated"
        exit 1
    else
        log_with_timestamp "RESOURCE MONITORING: All resources within normal limits"
        exit 0
    fi
}

main
EOF
    
    sudo mv /tmp/resource_monitor.sh $MONITOR_DIR/resource_monitor.sh
    sudo chmod +x $MONITOR_DIR/resource_monitor.sh
    
    success "Resource monitoring script created"
}

# Create log monitoring script
create_log_monitor() {
    log "Creating log monitoring script..."
    
    cat > /tmp/log_monitor.sh << 'EOF'
#!/bin/bash

# Log monitoring for AliranTunai
CONFIG_FILE="/etc/aliran-tunai/monitoring.conf"
MONITOR_LOG="/var/log/aliran-tunai/log_monitor.log"
APP_LOG="/var/log/aliran-tunai/app.log"

# Source configuration
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    ERROR_THRESHOLD_PER_HOUR=50
fi

# Function to log with timestamp
log_with_timestamp() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$MONITOR_LOG"
}

# Check for errors in the last hour
check_recent_errors() {
    if [ ! -f "$APP_LOG" ]; then
        log_with_timestamp "LOG MONITOR: Application log file not found"
        return 0
    fi
    
    # Get timestamp from 1 hour ago
    ONE_HOUR_AGO=$(date -d '1 hour ago' '+%Y-%m-%d %H:%M:%S')
    
    # Count errors in the last hour
    ERROR_COUNT=$(awk -v start_time="$ONE_HOUR_AGO" '
        $1 " " $2 >= start_time && /ERROR|CRITICAL|FATAL/ { count++ }
        END { print count+0 }
    ' "$APP_LOG")
    
    if [ "$ERROR_COUNT" -gt "$ERROR_THRESHOLD_PER_HOUR" ]; then
        log_with_timestamp "LOG MONITOR: HIGH ERROR COUNT: $ERROR_COUNT errors in the last hour (threshold: $ERROR_THRESHOLD_PER_HOUR)"
        return 1
    else
        log_with_timestamp "LOG MONITOR: Error count within normal limits: $ERROR_COUNT errors in the last hour"
        return 0
    fi
}

# Main function
main() {
    if ! check_recent_errors; then
        exit 1
    fi
    exit 0
}

main
EOF
    
    sudo mv /tmp/log_monitor.sh $MONITOR_DIR/log_monitor.sh
    sudo chmod +x $MONITOR_DIR/log_monitor.sh
    
    success "Log monitoring script created"
}

# Setup cron jobs for monitoring
setup_cron_jobs() {
    log "Setting up monitoring cron jobs..."
    
    # Create cron jobs for ubuntu user
    (crontab -l 2>/dev/null || true; cat << EOF

# AliranTunai Monitoring Jobs
# Resource monitoring every 5 minutes
*/5 * * * * $MONITOR_DIR/resource_monitor.sh

# Log monitoring every 10 minutes
*/10 * * * * $MONITOR_DIR/log_monitor.sh

# Daily cleanup of old logs
0 2 * * * find /var/log/aliran-tunai -name "*.log" -mtime +30 -delete

# Weekly health report
0 8 * * 1 /opt/aliran-tunai/current/venv/bin/python /opt/aliran-tunai/current/scripts/health_check.py > /var/log/aliran-tunai/weekly_health_report.txt 2>&1

EOF
    ) | crontab -
    
    success "Monitoring cron jobs configured"
}

# Create logrotate configuration
setup_log_rotation() {
    log "Setting up log rotation..."
    
    cat > /tmp/aliran-tunai-logrotate << EOF
/var/log/aliran-tunai/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload aliran-tunai >/dev/null 2>&1 || true
        systemctl reload aliran-whatsapp >/dev/null 2>&1 || true
    endscript
}
EOF
    
    sudo mv /tmp/aliran-tunai-logrotate /etc/logrotate.d/aliran-tunai
    
    success "Log rotation configured"
}

# Create monitoring dashboard script
create_dashboard() {
    log "Creating monitoring dashboard script..."
    
    cat > /tmp/dashboard.py << 'EOF'
#!/usr/bin/env python3
"""
Simple monitoring dashboard for AliranTunai
Displays real-time status of all monitored components
"""

import os
import json
import time
import subprocess
from datetime import datetime

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def get_service_status(service_name):
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except:
        return 'unknown'

def get_system_stats():
    try:
        # CPU usage
        cpu_result = subprocess.run(
            ['top', '-bn1'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Memory usage
        memory_result = subprocess.run(
            ['free', '-h'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Disk usage
        disk_result = subprocess.run(
            ['df', '-h', '/'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return {
            'cpu': cpu_result.stdout,
            'memory': memory_result.stdout,
            'disk': disk_result.stdout
        }
    except:
        return None

def display_dashboard():
    while True:
        clear_screen()
        
        print("=" * 60)
        print("     AliranTunai Monitoring Dashboard")
        print("=" * 60)
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Service Status
        print("🔧 SERVICES STATUS")
        print("-" * 30)
        services = ['aliran-tunai', 'aliran-whatsapp', 'nginx', 'mongodb']
        for service in services:
            status = get_service_status(service)
            icon = "✅" if status == 'active' else "❌"
            print(f"{icon} {service:<20} {status}")
        
        print()
        
        # Health Check Status
        print("🏥 HEALTH CHECK STATUS")
        print("-" * 30)
        health_report_path = '/var/log/aliran-tunai/health_report.json'
        try:
            if os.path.exists(health_report_path):
                with open(health_report_path, 'r') as f:
                    health_data = json.load(f)
                
                overall_status = health_data.get('overall_status', 'unknown')
                icon = "✅" if overall_status == 'healthy' else "⚠️"
                print(f"{icon} Overall Status: {overall_status.upper()}")
                
                checks_passed = health_data.get('checks_passed', 0)
                total_checks = health_data.get('total_checks', 0)
                print(f"📊 Checks Passed: {checks_passed}/{total_checks}")
            else:
                print("❓ Health report not available")
        except Exception as e:
            print(f"❌ Error reading health report: {str(e)}")
        
        print()
        
        # System Resources
        print("💻 SYSTEM RESOURCES")
        print("-" * 30)
        stats = get_system_stats()
        if stats:
            # Parse CPU usage from top command
            cpu_line = [line for line in stats['cpu'].split('\n') if 'Cpu(s)' in line]
            if cpu_line:
                print(f"🖥️  CPU: {cpu_line[0].strip()}")
            
            # Parse memory usage
            memory_lines = stats['memory'].split('\n')
            if len(memory_lines) > 1:
                print(f"💾 Memory: {memory_lines[1].strip()}")
            
            # Parse disk usage
            disk_lines = stats['disk'].split('\n')
            if len(disk_lines) > 1:
                print(f"💿 Disk: {disk_lines[1].strip()}")
        else:
            print("❌ Unable to retrieve system stats")
        
        print()
        print("Press Ctrl+C to exit | Refreshes every 10 seconds")
        print("=" * 60)
        
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            print("\nExiting dashboard...")
            break

if __name__ == '__main__':
    display_dashboard()
EOF
    
    sudo mv /tmp/dashboard.py $MONITOR_DIR/dashboard.py
    sudo chmod +x $MONITOR_DIR/dashboard.py
    
    success "Monitoring dashboard created"
}

# Main setup function
main() {
    log "Setting up AliranTunai monitoring system..."
    
    setup_directories
    create_monitoring_config
    create_health_check_service
    create_resource_monitor
    create_log_monitor
    setup_cron_jobs
    setup_log_rotation
    create_dashboard
    
    success "Monitoring system setup completed successfully!"
    
    log "Available monitoring commands:"
    echo "- View dashboard: $MONITOR_DIR/dashboard.py"
    echo "- Run health check: /opt/aliran-tunai/current/scripts/health_check.py"
    echo "- Check resource usage: $MONITOR_DIR/resource_monitor.sh"
    echo "- Monitor logs: $MONITOR_DIR/log_monitor.sh"
    echo "- View health check timer: sudo systemctl status aliran-health-check.timer"
    echo "- View monitoring logs: tail -f /var/log/aliran-tunai/*.log"
    
    if [ -n "$ALERT_EMAIL" ]; then
        log "Email alerts will be sent to: $ALERT_EMAIL"
    else
        warning "No alert email configured. Update /etc/aliran-tunai/monitoring.conf to enable email alerts."
    fi
}

# Run main function
main "$@"