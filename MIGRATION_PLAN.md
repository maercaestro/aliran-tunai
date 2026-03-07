# AliranTunai VM Migration Plan — EC2 to GCloud

> **Date:** 7 March 2026  
> **From:** AWS EC2 (old VM — no access)  
> **To:** Google Cloud Compute Engine (Ubuntu 22.04)  
> **VM User:** `abuhuzaifahbidin`  
> **Instance:** `furnace-pinn-vm`

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Credential Recovery](#2-credential-recovery)
3. [GCloud VM Setup](#3-gcloud-vm-setup)
4. [Deploy Application](#4-deploy-application)
5. [DNS & Domain Updates](#5-dns--domain-updates)
6. [SSL Certificate](#6-ssl-certificate)
7. [WhatsApp Webhook Update](#7-whatsapp-webhook-update)
8. [Frontend (Vercel) Update](#8-frontend-vercel-update)
9. [GitHub Actions Secrets Update](#9-github-actions-secrets-update)
10. [Verification Checklist](#10-verification-checklist)

---

## 1. Architecture Overview

| Component | File | Port | Service |
|-----------|------|------|---------|
| API Server (Dashboard/Auth) | `api_server.py` | 5001 | `aliran-api-server` |
| WhatsApp Bot | `whatsapp_business_api.py` | 5002 | `aliran-whatsapp` |
| Telegram Bot | `main.py` | — | `aliran-tunai` |
| Frontend (React) | `frontend/` | — | Hosted on Vercel |
| Reverse Proxy | nginx | 80/443 | System nginx |

**External Services (no migration needed):**
- MongoDB Atlas (cloud database)
- OpenAI API
- Meta WhatsApp Business API
- Vercel (frontend hosting)

---

## 2. Credential Recovery

Since you can't access the old VM, recover all credentials from their source:

### 2.1 — MongoDB

| Credential | Where to Get |
|---|---|
| `MONGO_URI` | [MongoDB Atlas](https://cloud.mongodb.com) → Your Project → **Connect** → **Drivers** → Copy connection string |

> Your data is safe — it's in Atlas cloud, not on the old VM.

### 2.2 — OpenAI

| Credential | Where to Get |
|---|---|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) → **Create new secret key** |

### 2.3 — WhatsApp Business API ⚠️

**No new phone number needed!** Everything lives in Meta's cloud.

| Credential | Where to Get |
|---|---|
| `WHATSAPP_ACCESS_TOKEN` | Meta Developer Console → Your App → **WhatsApp** → **API Setup** (see below for permanent token) |
| `WHATSAPP_PHONE_NUMBER_ID` | Same page — shown under "Phone number ID" |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | Meta **Business Settings** → **Accounts** → **WhatsApp Accounts** |
| `WHATSAPP_VERIFY_TOKEN` | Set any new string you want (e.g., `aliran_verify_2026`) |
| `WHATSAPP_API_VERSION` | `v18.0` (or latest) |

#### Getting a Permanent Access Token:

1. Go to [business.facebook.com](https://business.facebook.com) → **Business Settings**
2. **Users** → **System Users** → Select/create a system user
3. Click **Generate New Token**
4. Select your WhatsApp app
5. Enable permissions:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
6. Copy the token — this one **does not expire**

### 2.4 — JWT & Other Keys

| Credential | How to Generate |
|---|---|
| `JWT_SECRET_KEY` | Run: `openssl rand -hex 32` |
| `TELEGRAM_BOT_TOKEN` | Message @BotFather on Telegram → `/token` |
| `WEBHOOK_URL` | Will be your new domain URL |

### 2.5 — Assemble Your `.env`

```env
# --- Database ---
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority

# --- WhatsApp Business API ---
WHATSAPP_ACCESS_TOKEN=<permanent_token_from_meta>
WHATSAPP_PHONE_NUMBER_ID=<from_meta_dashboard>
WHATSAPP_BUSINESS_ACCOUNT_ID=<from_meta_business_settings>
WHATSAPP_API_VERSION=v18.0
WHATSAPP_VERIFY_TOKEN=<your_new_verify_token>
WHATSAPP_PORT=5002

# --- OpenAI ---
OPENAI_API_KEY=sk-<your_new_key>

# --- JWT ---
JWT_SECRET_KEY=<output_of_openssl_rand>

# --- Telegram ---
TELEGRAM_BOT_TOKEN=<from_botfather>
WEBHOOK_URL=https://api.aliran-tunai.com/webhook

# --- Flask ---
FLASK_ENV=production
FLASK_DEBUG=False

# --- Feature Flags ---
ENABLE_PERSONAL_BUDGET=true
ENABLE_BUSINESS=true
DEFAULT_MODE=business
ALLOW_MODE_SWITCHING=true
```

---

## 3. GCloud VM Setup

### 3.1 — SSH into VM

```bash
gcloud compute ssh furnace-pinn-vm --zone=<YOUR_ZONE>
```

### 3.2 — Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3 python3-pip python3-venv python3-dev \
    build-essential nginx git curl wget \
    tesseract-ocr tesseract-ocr-eng \
    certbot python3-certbot-nginx
```

### 3.3 — Open Firewall Ports

```bash
# GCloud firewall (from your local machine or GCloud Console)
gcloud compute firewall-rules create allow-http-https \
    --allow tcp:80,tcp:443 \
    --target-tags=http-server,https-server

# Also add the tags to your VM
gcloud compute instances add-tags furnace-pinn-vm \
    --tags=http-server,https-server \
    --zone=<YOUR_ZONE>
```

---

## 4. Deploy Application

### 4.1 — Create App Directory

```bash
sudo mkdir -p /opt/aliran-tunai/{current,backup}
sudo mkdir -p /var/log/aliran-tunai
sudo chown -R $(whoami):$(whoami) /opt/aliran-tunai
sudo chown -R $(whoami):$(whoami) /var/log/aliran-tunai
```

### 4.2 — Clone Repository

```bash
cd /opt/aliran-tunai/current
git clone https://github.com/abuhuzaifahbidin/aliran-tunai.git .
```

### 4.3 — Setup Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.4 — Create `.env` File

```bash
nano /opt/aliran-tunai/current/.env
# Paste the .env contents from Section 2.5
```

### 4.5 — Install Systemd Services

```bash
cd /opt/aliran-tunai/current

# Copy service files (user is already set to abuhuzaifahbidin)
sudo cp deploy/aliran-api-server.service /etc/systemd/system/
sudo cp deploy/aliran-whatsapp.service /etc/systemd/system/
sudo cp deploy/aliran-tunai.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable aliran-api-server aliran-whatsapp aliran-tunai
sudo systemctl start aliran-api-server aliran-whatsapp aliran-tunai

# Verify
sudo systemctl status aliran-api-server aliran-whatsapp aliran-tunai
```

### 4.6 — Setup Nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/aliran-tunai

# Replace placeholder domain with your actual domain
sudo sed -i 's/your-domain.com/api.aliran-tunai.com/g' /etc/nginx/sites-available/aliran-tunai

# Enable site
sudo ln -sf /etc/nginx/sites-available/aliran-tunai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and restart
sudo nginx -t
sudo systemctl restart nginx
```

---

## 5. DNS & Domain Updates

You need to update **2 DNS records** to point to the new VM's external IP.

### 5.1 — Get New VM's External IP

```bash
gcloud compute instances describe furnace-pinn-vm \
    --zone=<YOUR_ZONE> \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

### 5.2 — Update DNS A Records

Go to your domain registrar/DNS provider and update:

| Record Type | Host/Name | Old Value (EC2 IP) | New Value (GCloud IP) |
|---|---|---|---|
| A | `api.aliran-tunai.com` | old EC2 IP | `<NEW_GCLOUD_IP>` |
| A | `aliran-tunai.com` (if applicable) | old EC2 IP | `<NEW_GCLOUD_IP>` |

> **TTL Tip:** If possible, lower the TTL to 300 (5 min) before the switch so DNS propagates faster. After it's stable, set it back to 3600.

### 5.3 — Verify DNS Propagation

```bash
# Check from your local machine
dig api.aliran-tunai.com +short
nslookup api.aliran-tunai.com

# Should return your new GCloud IP
```

---

## 6. SSL Certificate

After DNS propagates (wait a few minutes):

```bash
# On the GCloud VM
sudo certbot --nginx -d api.aliran-tunai.com

# Auto-renew (should be set up automatically, but verify)
sudo certbot renew --dry-run
```

---

## 7. WhatsApp Webhook Update

Once SSL is active and the API is reachable:

1. Go to [developers.facebook.com](https://developers.facebook.com) → Your App
2. **WhatsApp** → **Configuration**
3. Under **Webhook**:
   - **Callback URL:** `https://api.aliran-tunai.com/whatsapp/webhook`
   - **Verify Token:** your new `WHATSAPP_VERIFY_TOKEN` from `.env`
4. Click **Verify and Save**
5. Under **Webhook Fields**, ensure these are subscribed:
   - `messages`
   - `message_deliveries` (optional)

### Test It:

```bash
# From your local machine
curl "https://api.aliran-tunai.com/whatsapp/webhook?hub.verify_token=YOUR_TOKEN&hub.challenge=test123&hub.mode=subscribe"
# Should return: test123
```

---

## 8. Frontend (Vercel) Update

The frontend at `flow-ai.biz` points to `https://api.aliran-tunai.com` (see `frontend/src/config/api.js`).

**If the domain stays the same (`api.aliran-tunai.com`):**
- ✅ No frontend changes needed — once DNS updates, it auto-points to new VM

**If you change the API domain:**
- Update `frontend/src/config/api.js` line 8:
  ```js
  : 'https://your-new-api-domain.com'
  ```
- Update CORS in `api_server.py` line 37 if frontend domain changes
- Redeploy frontend on Vercel

---

## 9. GitHub Actions Secrets Update

Go to **GitHub** → Your Repo → **Settings** → **Secrets and variables** → **Actions**

### Remove old EC2 secrets:
- `EC2_HOST`
- `EC2_SSH_PRIVATE_KEY`

### Add new GCloud secrets:

| Secret | Value |
|---|---|
| `GCP_PROJECT_ID` | Your GCloud project ID |
| `GCP_SA_KEY` | Service Account JSON key (see below) |
| `GCE_INSTANCE` | `furnace-pinn-vm` |
| `GCE_ZONE` | Your VM zone (e.g., `asia-southeast1-a`) |

### Keep/update these secrets:
| Secret | Action |
|---|---|
| `MONGO_URI` | Keep same (or update if changed) |
| `OPENAI_API_KEY` | Update with new key |
| `WHATSAPP_ACCESS_TOKEN` | Update with new permanent token |
| `WHATSAPP_PHONE_NUMBER_ID` | Keep same |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | Keep same |
| `WHATSAPP_API_VERSION` | Keep `v18.0` |
| `WHATSAPP_VERIFY_TOKEN` | Update with new verify token |
| `JWT_SECRET_KEY` | Update with new generated key |

### Create GCloud Service Account:

```bash
# Create service account
gcloud iam service-accounts create aliran-deployer \
    --display-name="Aliran Deployer"

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:aliran-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/compute.instanceAdmin.v1"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:aliran-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iap.tunnelResourceAccessor"

# Generate key
gcloud iam service-accounts keys create gcp-sa-key.json \
    --iam-account=aliran-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Copy contents of gcp-sa-key.json → paste into GCP_SA_KEY GitHub secret
cat gcp-sa-key.json
```

---

## 10. Verification Checklist

Run through each item after migration:

| # | Check | Command / Action | Status |
|---|---|---|---|
| 1 | VM is running | `gcloud compute instances list` | ☐ |
| 2 | Services are active | `sudo systemctl status aliran-api-server aliran-whatsapp` | ☐ |
| 3 | API health check | `curl https://api.aliran-tunai.com/health` | ☐ |
| 4 | WhatsApp health | `curl http://localhost:5002/health` (on VM) | ☐ |
| 5 | DNS points to new IP | `dig api.aliran-tunai.com +short` | ☐ |
| 6 | SSL is valid | `curl -vI https://api.aliran-tunai.com 2>&1 \| grep "SSL certificate"` | ☐ |
| 7 | WhatsApp webhook verified | Meta Developer Console shows ✅ | ☐ |
| 8 | Send test WhatsApp message | Message the bot, check it replies | ☐ |
| 9 | Frontend login works | Go to `flow-ai.biz`, try OTP login | ☐ |
| 10 | Dashboard loads data | Login and view dashboard | ☐ |
| 11 | OTP delivery works | Login with a friend's number | ☐ |
| 12 | GitHub Actions deploy works | Push a small commit to `main` | ☐ |
| 13 | Rollback works | Verify `/opt/aliran-tunai/backup` exists | ☐ |

---

## Order of Operations (Recommended)

```
1. Recover all credentials (Section 2)          ← Do first, no VM needed
2. Setup GCloud VM (Section 3)
3. Deploy application (Section 4)
4. Test locally on VM (curl localhost:5001/health)
5. Update DNS A records (Section 5)             ← Start DNS propagation
6. Wait for DNS propagation (~5-30 min)
7. Setup SSL certificate (Section 6)
8. Update WhatsApp webhook (Section 7)
9. Test everything end-to-end (Section 10)
10. Update GitHub Secrets (Section 9)
11. Push a commit to test CI/CD
```

> **Total estimated time:** 1-2 hours (excluding DNS propagation wait)
