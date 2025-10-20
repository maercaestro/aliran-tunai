# Environment Variable Setup for Personal Budget Feature

The 403 error you're experiencing is because the `ENABLE_PERSONAL_BUDGET` environment variable is not set to `true` on your production server.

## Required Environment Variables

Add these environment variables to your production deployment:

```bash
ENABLE_PERSONAL_BUDGET=true
```

## Setup Instructions by Platform:

### Railway Deployment
1. Go to your Railway project dashboard
2. Navigate to the "Variables" tab
3. Add new environment variable:
   - Key: `ENABLE_PERSONAL_BUDGET`
   - Value: `true`
4. Redeploy your application

### Heroku Deployment
```bash
heroku config:set ENABLE_PERSONAL_BUDGET=true -a your-app-name
```

### VPS/Direct Server Deployment
Add to your systemd service file or environment configuration:
```bash
Environment=ENABLE_PERSONAL_BUDGET=true
```

### PM2 Deployment
Update your `ecosystem.config.js`:
```javascript
module.exports = {
  apps: [{
    name: 'aliran-tunai',
    script: 'main.py',
    env: {
      ENABLE_PERSONAL_BUDGET: 'true'
    }
  }]
}
```

## Verify Setup
After setting the environment variable and redeploying, test by accessing:
```
https://your-domain.com/api/personal/dashboard/YOUR_PHONE_NUMBER
```

It should no longer return a 403 error.