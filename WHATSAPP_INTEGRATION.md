# WhatsApp Business API Integration Setup Guide

This guide explains how to set up and handle the WhatsApp integration for the Aliran Tunai financial tracking system.

## 📱 Current WhatsApp Architecture

### **How It Works:**
1. **WhatsApp Business API** receives messages via webhook
2. **AI Processing** extracts financial transaction data
3. **Mode-Aware Responses** based on user's personal/business mode
4. **Database Storage** saves transactions and user preferences
5. **Smart Suggestions** for mode switching based on patterns

## 🔧 Setup Requirements

### **1. WhatsApp Business API Account**
You need a Facebook Business account with WhatsApp Business API access:

```bash
# Required Environment Variables
WHATSAPP_ACCESS_TOKEN="your_permanent_access_token"
WHATSAPP_PHONE_NUMBER_ID="your_phone_number_id" 
WHATSAPP_BUSINESS_ACCOUNT_ID="your_business_account_id"
WHATSAPP_API_VERSION="v23.0"
WHATSAPP_VERIFY_TOKEN="your_custom_verify_token"
```

### **2. Webhook Configuration**
Set your webhook URL in Facebook Developer Console:
```
Webhook URL: https://your-domain.com/whatsapp/webhook
Verify Token: your_custom_verify_token (from env)
```

### **3. Current Webhook Endpoints**

#### **GET /whatsapp/webhook** - Verification
```python
# Verifies webhook with Facebook
# Returns challenge token if verification successful
```

#### **POST /whatsapp/webhook** - Message Handler  
```python
# Processes incoming messages and images
# Handles text messages -> handle_message()
# Handles images -> handle_media_message()
# Sends responses back via send_whatsapp_message()
```

## 📋 Available WhatsApp Commands

### **Mode Management:**
- `/mode` - Show current mode and options
- `/setpersonal` or `/personal` - Switch to personal budget mode
- `/setbusiness` or `/business` - Switch to business mode

### **Transaction & Status:**
- `/status` - Financial health report (shows current mode)
- `/summary` - Transaction summary
- `/streak` - Daily logging streak
- `/start` or `/help` - Welcome message

### **Utility:**
- `/test_db` - Test database connection

## 🤖 Message Processing Flow

```
WhatsApp Message → Webhook → Language Detection → Registration Check → Command/Transaction Processing → AI Response → Mode Suggestions → Send Reply
```

### **Example Interactions:**

**Personal Mode (Default):**
```
User: "beli nasi lemak rm 5"
Bot: ✅ Logged: Expense of RM 5.00 with Nasi Lemak vendor
     📦 Items: nasi lemak
     🔥 Streak extended! Current streak: 3 days
```

**Business Mode:**
```
User: "jual produk rm 150"
Bot: ✅ Logged: Sale of RM 150.00 with customer
     📦 Items: produk  
     🔥 Streak extended! Current streak: 3 days
```

**Mode Switching:**
```
User: "/mode"
Bot: 🔧 Mode Settings
     Current Mode: 💰 Personal Budget
     
     Available Modes:
     💰 Personal Budget - ✅ [ACTIVE]
     🏢 Business Tracking - 🔄 Available
     
     Switch Mode:
     • Type /setbusiness to switch to business mode
```

## 🚀 Deployment Options

### **Current Setup (EC2):**
Your system runs on EC2 with these services:
- `aliran-api-server.service` - Main API (port 5002)
- `aliran-whatsapp.service` - WhatsApp handler
- `nginx` - Reverse proxy

### **Testing Locally:**
```bash
# 1. Set environment variables in .env
# 2. Run WhatsApp webhook server
python whatsapp_business_api.py

# 3. Use ngrok for local testing
ngrok http 5000

# 4. Set webhook URL to ngrok URL + /whatsapp/webhook
```

### **Production Deployment:**
Current CI/CD automatically deploys to EC2 when you push to main branch.

## 🔄 How Your Mode Switching Works

### **1. User Registration:**
- New users start in `personal` mode by default
- Mode preference stored in MongoDB `users` collection
- Registration process is mode-aware

### **2. Mode Detection & Switching:**
```python
# Get user's current mode
current_mode = get_user_mode(wa_id)  # Returns 'personal' or 'business'

# Set new mode  
success = set_user_mode(wa_id, 'business')  # Stores in database
```

### **3. Smart Suggestions:**
The system analyzes transaction patterns and suggests mode switches:

**Business Indicators (suggests switching from personal):**
- Keywords: "jual", "customer", "inventory", "supplier"
- Large amounts (>RM 1000)
- Business actions: sale, purchase, payment_received

**Personal Indicators (suggests switching from business):**
- Keywords: "makan", "grab", "petrol", "gaji"
- Small amounts (<RM 100)  
- Personal actions: income, expense, transfer, saving

## 📊 Current Status

### **✅ Working Features:**
- WhatsApp Business API integration
- Mode switching commands (/setpersonal, /setbusiness, /mode)
- Smart mode suggestions
- Per-user mode storage in database
- Multi-language support (EN/MS)
- Image receipt processing
- Transaction categorization by mode

### **🔧 To Test:**
1. **Send a WhatsApp message** to your business number
2. **Try mode commands** like `/mode` or `/setpersonal`
3. **Send transactions** like "beli nasi lemak rm 5"
4. **Check mode suggestions** when using wrong mode for transaction type

### **📝 Environment Check:**
Your `.env` file has all required WhatsApp credentials set. The system should work once your webhook is properly configured with Facebook.

## 🐛 Troubleshooting

### **Common Issues:**
1. **Webhook not receiving messages** - Check Facebook webhook settings
2. **Access token expired** - Generate new permanent token
3. **Messages not sending** - Verify WHATSAPP_ACCESS_TOKEN and PHONE_NUMBER_ID
4. **Mode switching fails** - User must be registered first

### **Debug Commands:**
```bash
# Check webhook status
curl "https://your-domain.com/whatsapp/webhook?hub.verify_token=your_token&hub.challenge=test&hub.mode=subscribe"

# Test database connection via WhatsApp
# Send message: /test_db
```

Your WhatsApp integration is comprehensive and ready for production use! 🚀