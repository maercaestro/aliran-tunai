# 🚂 Railway Deployment Guide

## Quick Deploy Steps:

### 1. Push to GitHub
```bash
git add .
git commit -m "Railway deployment ready"
git push origin main
```

### 2. Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `aliran-tunai` repository
4. Railway will automatically detect Python and deploy

### 3. Set Environment Variables
In Railway dashboard, go to Variables tab and add:
```
TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
MONGO_URI=your_mongodb_atlas_uri
WEBHOOK_URL=https://your-app-name.railway.app
```

### 4. Get Your Railway URL
- Railway will give you a URL like: `https://aliran-tunai-production-xyz.railway.app`
- Copy this URL and set it as your `WEBHOOK_URL`

### 5. Set Webhook
```bash
# After deployment is complete:
curl -X POST https://your-railway-url.railway.app/set_webhook
```

## Fixed Issues:
✅ OpenCV headless version (no GUI dependencies)
✅ System libraries configured via nixpacks.toml
✅ PORT environment variable handling
✅ Procfile for process management
✅ Runtime specified for Python 3.12

## Health Check:
Visit: `https://your-railway-url.railway.app/health`

## Files Added for Railway:
- `Procfile` - Process definition
- `runtime.txt` - Python version
- `railway.toml` - Railway configuration
- `nixpacks.toml` - System dependencies
- Updated `requirements.txt` - Headless OpenCV
