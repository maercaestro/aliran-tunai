# EC2 Deployment Guide for AliranTunai Bot

This guide will help you deploy the AliranTunai Telegram bot to AWS EC2 with webhook functionality.

## Prerequisites

1. AWS EC2 instance (Ubuntu 20.04 LTS or newer)
2. Domain name or use EC2 public IP
3. SSL certificate (Let's Encrypt recommended)
4. Security Group configured for HTTP/HTTPS traffic

## Step 1: Launch EC2 Instance

1. **Launch EC2 Instance:**
   - AMI: Ubuntu Server 20.04 LTS
   - Instance Type: t3.micro (or larger based on usage)
   - Storage: 8GB minimum
   - Security Group: Create new with ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8443 (webhook)

2. **Connect to instance:**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-public-ip
   ```

## Step 2: Setup Environment

1. **Update system:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Python and dependencies:**
   ```bash
   sudo apt install python3 python3-pip python3-venv nginx git curl -y
   sudo apt install tesseract-ocr -y  # For OCR functionality
   ```

3. **Install Node.js (for frontend if needed):**
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

## Step 3: Clone and Setup Application

1. **Clone repository:**
   ```bash
   git clone https://github.com/maercaestro/aliran-tunai.git
   cd aliran-tunai
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file:**
   ```bash
   cp .env.example .env
   nano .env
   ```

   Fill in your environment variables:
   ```
   TELEGRAM_TOKEN=your_bot_token
   OPENAI_API_KEY=your_openai_key
   MONGO_URI=your_mongodb_uri
   WEBHOOK_URL=https://your-domain.com
   WEBHOOK_PORT=8443
   ```

## Step 4: Setup Nginx Reverse Proxy

1. **Create Nginx configuration:**
   ```bash
   sudo nano /etc/nginx/sites-available/aliran-tunai
   ```

   Add configuration:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;  # Replace with your domain or EC2 public IP
       
       location / {
           proxy_pass http://localhost:8443;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

2. **Enable the site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/aliran-tunai /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## Step 5: Setup SSL (Optional but Recommended)

1. **Install Certbot:**
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   ```

2. **Get SSL certificate:**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

## Step 6: Create Systemd Service

1. **Create service file:**
   ```bash
   sudo nano /etc/systemd/system/aliran-tunai.service
   ```

   Add service configuration (see aliran-tunai.service file)

2. **Enable and start service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable aliran-tunai
   sudo systemctl start aliran-tunai
   ```

## Step 7: Setup Webhook

1. **Test the application:**
   ```bash
   sudo systemctl status aliran-tunai
   curl http://localhost:8443/health
   ```

2. **Set webhook URL:**
   ```bash
   curl -X POST https://your-domain.com/set_webhook
   ```

   Or manually via Telegram API:
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://your-domain.com/webhook"}'
   ```

## Step 8: Monitor and Maintain

1. **Check logs:**
   ```bash
   sudo journalctl -u aliran-tunai -f
   ```

2. **Restart service:**
   ```bash
   sudo systemctl restart aliran-tunai
   ```

3. **Update application:**
   ```bash
   cd /home/ubuntu/aliran-tunai
   git pull origin main
   source venv/bin/activate
   pip install -r requirements.txt
   sudo systemctl restart aliran-tunai
   ```

## Firewall Configuration

```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 8443
```

## Environment Variables

Make sure these are set in your `.env` file:
- `TELEGRAM_TOKEN`: Your bot token from BotFather
- `OPENAI_API_KEY`: Your OpenAI API key
- `MONGO_URI`: Your MongoDB Atlas connection string
- `WEBHOOK_URL`: Your domain (e.g., https://your-domain.com)
- `WEBHOOK_PORT`: Port for the Flask app (8443)

## Troubleshooting

1. **Check service status:**
   ```bash
   sudo systemctl status aliran-tunai
   ```

2. **Check logs:**
   ```bash
   sudo journalctl -u aliran-tunai -n 50
   ```

3. **Test webhook:**
   ```bash
   curl -X POST https://your-domain.com/webhook -H "Content-Type: application/json" -d '{}'
   ```

4. **Verify Telegram webhook:**
   ```bash
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
   ```
