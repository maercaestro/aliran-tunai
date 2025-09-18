# AliranTunai CI/CD Pipeline Documentation

## Overview

This document describes the comprehensive CI/CD pipeline implemented for AliranTunai, a financial transaction tracking bot with Telegram and WhatsApp integrations.

## Architecture

### Backend Services
- **Telegram Bot** (`main.py`) - Core bot functionality
- **WhatsApp Business API** (`whatsapp_business_api.py`) - Flask-based webhook handler
- **MongoDB** - Transaction data storage
- **External APIs** - OpenAI, Telegram, WhatsApp

### Infrastructure
- **EC2 Deployment** - Production environment on AWS
- **Nginx** - Reverse proxy and load balancer
- **SystemD** - Service management
- **MongoDB** - Database (Atlas or self-hosted)

## CI/CD Pipeline Components

### 1. Testing Pipeline (`.github/workflows/ci-cd.yml`)

#### **Backend Testing**
- **Environment Setup**
  - Python 3.12
  - MongoDB test container
  - System dependencies (Tesseract OCR)

- **Code Quality Checks**
  - **Black** - Code formatting
  - **isort** - Import sorting
  - **Flake8** - Linting
  - **MyPy** - Type checking
  - **Bandit** - Security analysis
  - **Safety** - Vulnerability scanning

- **Testing Levels**
  - **Unit Tests** (`tests/`) - Individual component testing
  - **Integration Tests** (`integration_tests/`) - End-to-end workflow testing
  - **Environment Validation** - Comprehensive dependency checking

#### **Test Coverage**
- Code coverage reporting with **Codecov**
- HTML and XML coverage reports
- Coverage threshold monitoring

### 2. Deployment Pipeline

#### **Automated Deployment (Main Branch)**
- **Pre-deployment Validation**
  - All tests must pass
  - Environment validation
  - Health checks

- **Deployment Process**
  - Secure file transfer to EC2
  - Zero-downtime deployment
  - Service restart with health checks
  - Rollback capability on failure

#### **Manual Deployment Scripts**
- **`deploy/deploy.sh`** - Complete deployment setup
- **`deploy/setup_monitoring.sh`** - Monitoring system setup

### 3. Monitoring & Health Checks

#### **Health Check Scripts**
- **`scripts/health_check.py`** - Comprehensive health monitoring
  - SystemD service status
  - API endpoint testing
  - Database connectivity
  - External API validation
  - System resource monitoring
  - Log file analysis

- **`scripts/validate_environment.py`** - Environment validation
  - Python version compatibility
  - Package dependency verification
  - System dependency checking
  - Environment variable validation
  - Network connectivity testing

#### **Monitoring Dashboard**
- Real-time service status
- System resource utilization
- Health check history
- Alert management

## Setup Instructions

### 1. GitHub Repository Setup

#### **Required Secrets**
Configure these secrets in your GitHub repository settings:

```bash
# EC2 Configuration
EC2_HOST=your-ec2-public-ip-or-domain
EC2_SSH_PRIVATE_KEY=your-private-key-content

# Application Configuration
MONGO_URI=your-mongodb-connection-string
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
OPENAI_API_KEY=your-openai-api-key
WHATSAPP_VERIFY_TOKEN=your-whatsapp-verify-token
WHATSAPP_ACCESS_TOKEN=your-whatsapp-access-token
WHATSAPP_PHONE_NUMBER_ID=your-whatsapp-phone-number-id
```

#### **Branch Protection Rules**
1. Require status checks to pass before merging
2. Require branches to be up to date before merging
3. Require linear history

### 2. EC2 Server Setup

#### **Initial Setup**
```bash
# Clone repository
git clone https://github.com/your-username/aliran-tunai.git
cd aliran-tunai

# Run deployment script
sudo chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

#### **Manual Configuration**
```bash
# Install system dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx git tesseract-ocr -y

# Setup application
sudo mkdir -p /opt/aliran-tunai
sudo chown ubuntu:ubuntu /opt/aliran-tunai
cp -r . /opt/aliran-tunai/current/

# Setup Python environment
cd /opt/aliran-tunai/current
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Configuration

#### **Production Environment File**
Create `/opt/aliran-tunai/current/.env`:

```bash
# Database
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/database

# Telegram
TELEGRAM_BOT_TOKEN=your_actual_bot_token

# OpenAI
OPENAI_API_KEY=your_actual_openai_key

# WhatsApp
WHATSAPP_VERIFY_TOKEN=your_verify_token
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id

# Flask
FLASK_ENV=production
```

### 4. Service Management

#### **SystemD Services**
```bash
# Check service status
sudo systemctl status aliran-tunai aliran-whatsapp

# Start services
sudo systemctl start aliran-tunai aliran-whatsapp

# Enable auto-start
sudo systemctl enable aliran-tunai aliran-whatsapp

# View logs
sudo journalctl -u aliran-tunai -f
sudo journalctl -u aliran-whatsapp -f
```

#### **Nginx Configuration**
```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# Check status
sudo systemctl status nginx
```

## Monitoring and Maintenance

### 1. Health Monitoring

#### **Automated Health Checks**
```bash
# Run health check manually
python scripts/health_check.py

# View health check logs
sudo journalctl -u aliran-health-check -f

# Check timer status
sudo systemctl status aliran-health-check.timer
```

#### **Monitoring Dashboard**
```bash
# Launch interactive dashboard
/opt/aliran-tunai/monitoring/dashboard.py
```

### 2. Log Management

#### **Log Locations**
- **Application Logs**: `/var/log/aliran-tunai/`
- **System Logs**: `journalctl -u service-name`
- **Nginx Logs**: `/var/log/nginx/`
- **Health Check Logs**: `/var/log/aliran-tunai/health_report.json`

#### **Log Rotation**
- Automatic log rotation configured
- 30-day retention policy
- Compressed archives

### 3. Performance Monitoring

#### **Resource Monitoring**
- CPU usage tracking
- Memory utilization monitoring
- Disk space alerts
- Network connectivity checks

#### **Alert Thresholds**
- CPU usage > 80%
- Memory usage > 85%
- Disk usage > 90%
- Error rate > 50 errors/hour

## Troubleshooting

### Common Issues

#### **Deployment Failures**
1. Check GitHub Actions logs
2. Verify EC2 connectivity
3. Validate environment variables
4. Check service dependencies

```bash
# Debug deployment
ssh ubuntu@your-ec2-host
cd /opt/aliran-tunai/current
source venv/bin/activate
python scripts/validate_environment.py
```

#### **Service Issues**
```bash
# Check service status
sudo systemctl status aliran-tunai aliran-whatsapp

# View detailed logs
sudo journalctl -u aliran-tunai --since "1 hour ago"

# Restart services
sudo systemctl restart aliran-tunai aliran-whatsapp
```

#### **Database Connectivity**
```bash
# Test MongoDB connection
python test_mongodb.py

# Check connection from health script
python scripts/health_check.py
```

### Recovery Procedures

#### **Rollback Deployment**
```bash
# Manual rollback
cd /opt/aliran-tunai
sudo systemctl stop aliran-tunai aliran-whatsapp
sudo mv current current-failed
sudo mv backup current
sudo systemctl start aliran-tunai aliran-whatsapp
```

#### **Emergency Procedures**
1. Stop all services
2. Backup current state
3. Restore from known good backup
4. Restart services
5. Verify functionality

## Security Considerations

### 1. Access Control
- SSH key-based authentication
- Limited user privileges
- Firewall configuration
- Regular security updates

### 2. Data Protection
- Environment variable encryption
- Database connection security
- API token management
- Log sanitization

### 3. Network Security
- HTTPS enforcement
- Rate limiting
- Input validation
- CORS configuration

## Performance Optimization

### 1. Resource Management
- Memory limits for services
- CPU quotas
- Process monitoring
- Resource cleanup

### 2. Caching Strategy
- API response caching
- Database query optimization
- Static file caching
- CDN integration (for frontend)

## Backup and Recovery

### 1. Automated Backups
- Database backups
- Configuration backups
- Log archival
- Application state snapshots

### 2. Recovery Testing
- Regular recovery drills
- Backup validation
- RTO/RPO testing
- Documentation updates

---

## Quick Reference Commands

```bash
# Health check
python scripts/health_check.py

# Environment validation
python scripts/validate_environment.py

# Service status
sudo systemctl status aliran-tunai aliran-whatsapp

# View logs
sudo journalctl -u aliran-tunai -f

# Deploy manually
./deploy/deploy.sh

# Setup monitoring
./deploy/setup_monitoring.sh

# Dashboard
/opt/aliran-tunai/monitoring/dashboard.py
```

For additional support, refer to the individual component documentation or contact the development team.