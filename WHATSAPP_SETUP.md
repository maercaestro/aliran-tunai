# Aliran Tunai WhatsApp Business API Bot Setup Guide

This guide will help you set up the WhatsApp bot using the official WhatsApp Business API (no third-party services like Twilio).

## Prerequisites

1. **Meta Business Account**: Sign up at [business.facebook.com](https://business.facebook.com)
2. **WhatsApp Business API Access**: Apply for WhatsApp Business API through Meta
3. **Business-Registered WhatsApp Number**: A verified business phone number
4. **MongoDB Atlas**: Database for storing transaction data
5. **OpenAI API Key**: For AI-powered transaction parsing
6. **HTTPS Web Server**: Required for WhatsApp webhooks

## Step 1: WhatsApp Business API Setup

### 1.1 Create Meta Business Account
1. Go to [business.facebook.com](https://business.facebook.com)
2. Create a business account and verify your business

### 1.2 Apply for WhatsApp Business API
1. In your Meta Business account, go to **WhatsApp** → **API Setup**
2. Apply for WhatsApp Business API access
3. This process may take several days for approval

### 1.3 Get Your API Credentials
Once approved, you'll receive:
- **Access Token**: Permanent token for API access
- **Phone Number ID**: Unique identifier for your business number
- **Business Account ID**: Your WhatsApp Business Account ID

### 1.4 Set Up Webhook
1. In the WhatsApp Business API dashboard, configure your webhook:
   - **Webhook URL**: `https://yourdomain.com/whatsapp/webhook`
   - **Verify Token**: A secret token you create for webhook verification
2. Subscribe to these webhook fields:
   - `messages`
   - `message_deliveries`
   - `message_reads`

## Step 2: Environment Configuration

### 2.1 Copy Environment File
```bash
cp .env.whatsapp.example .env
```

### 2.2 Fill in Your Values
Edit the `.env` file with your actual credentials:

```env
# WhatsApp Business API Configuration
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_BUSINESS_ACCOUNT_ID=123456789012345
WHATSAPP_API_VERSION=v18.0
WHATSAPP_VERIFY_TOKEN=your_webhook_verify_token_here

# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_key_here

# MongoDB Configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/

# Flask Configuration
PORT=5000
```

## Step 3: Deploy the Bot

### 3.1 Install Dependencies
```bash
pip install -r requirements-whatsapp.txt
```

### 3.2 Run the Bot Locally (for testing)
```bash
python whatsapp_business_api.py
```

### 3.3 Deploy to Production
Deploy to your preferred platform (AWS EC2, Railway, Heroku, etc.) and ensure:
- The webhook URL is accessible from the internet (HTTPS required)
- Environment variables are set
- Port 5000 is exposed
- SSL certificate is properly configured

## Step 4: Test the Bot

### 4.1 Send Test Messages
1. From your WhatsApp, send a message to your business number
2. Try these commands:
   - `start` - Get welcome message
   - `status` - Get financial health report
   - `summary` - See recent transactions
   - `streak` - Check daily logging streak
   - `test_db` - Test database connection

### 4.2 Test Transaction Logging
Send messages like:
- "Beli nasi lemak 15 ringgit dari Restoran ABC"
- "Jual 10kg beras kepada Customer XYZ seharga 200"
- "Bayar supplier DEF 500 ringgit"

### 4.3 Test Receipt Processing
Send photos of receipts to automatically extract transaction data.

## Step 5: Webhook Verification

The bot includes automatic webhook verification. When you set up the webhook in Meta's dashboard, WhatsApp will send a GET request to verify your endpoint. The bot will automatically respond with the challenge if the verify token matches.

## Troubleshooting

### Common Issues:

1. **Webhook verification failed**
   - Ensure WHATSAPP_VERIFY_TOKEN matches what you set in Meta dashboard
   - Check that your server is running and accessible via HTTPS

2. **Messages not being received**
   - Verify webhook URL is correct and HTTPS
   - Check webhook subscription fields are enabled
   - Review Meta dashboard for webhook delivery errors

3. **API authentication errors**
   - Verify WHATSAPP_ACCESS_TOKEN is correct and not expired
   - Check WHATSAPP_PHONE_NUMBER_ID matches your business number

4. **Database connection failed**
   - Verify MongoDB URI format
   - Check IP whitelist in MongoDB Atlas
   - Ensure network connectivity

5. **OpenAI API errors**
   - Check API key validity and billing status
   - Verify rate limits haven't been exceeded

### Logs
Check the application logs for detailed error messages. The bot logs all activities including:
- Incoming webhook requests
- Message processing
- AI parsing results
- Database operations
- API call responses

## Features

The WhatsApp Business API bot includes all features from the Telegram version:
- ✅ AI-powered transaction parsing
- ✅ Financial health reports (CCC metrics)
- ✅ Daily logging streaks
- ✅ User data isolation
- ✅ Receipt photo processing with OCR
- ✅ Multi-language support (Malay/English)
- ✅ Real-time message responses
- ✅ Automatic message read receipts

## Security Notes

- All user data is isolated by WhatsApp ID
- Messages are processed in real-time and not stored
- Only transaction data is persisted in MongoDB
- API keys are encrypted in environment variables
- Webhook verification prevents unauthorized access

## API Limits and Costs

- **WhatsApp Business API**: Pay-as-you-go pricing based on conversations
- **OpenAI API**: Costs per token used for AI parsing
- **MongoDB Atlas**: Free tier available, paid plans for production
- **Server Hosting**: Costs vary by provider (AWS EC2, etc.)

## Support

For issues with:
- **WhatsApp Business API**: Check Meta for Developers documentation
- **Bot functionality**: Check application logs and error messages
- **AI parsing**: Verify OpenAI API key and billing status
- **Database**: Check MongoDB Atlas dashboard and connection strings

## Migration from Twilio

If you're migrating from the Twilio version:
1. Update your environment variables (remove Twilio, add WhatsApp Business API credentials)
2. Update requirements.txt (remove twilio, ensure requests is included)
3. Use the new `whatsapp_business_api.py` file instead of `whatsapp_bot.py`
4. Update webhook URL in Meta dashboard instead of Twilio console
5. Test thoroughly before going live
