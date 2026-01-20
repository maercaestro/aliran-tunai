# WhatsApp Authentication Template Setup Guide

## Overview
This guide shows you how to create a WhatsApp Authentication Template for sending OTP codes without the 24-hour messaging window restriction.

## Step 1: Access Meta Business Suite

1. Go to [Meta Business Suite](https://business.facebook.com/)
2. Select your WhatsApp Business Account
3. Navigate to **WhatsApp Manager** → **Message Templates**

## Step 2: Create New Template

Click **"Create Template"** and fill in:

### Basic Information
- **Template Name:** `otp_login`
- **Category:** `AUTHENTICATION`
- **Languages:** English (add more languages as needed)

### Message Content

**Header:** (Optional - leave empty or add your logo)

**Body:**
```
Your {{1}} verification code is *{{2}}*.

This code expires in {{3}} minutes. Do not share this code with anyone.
```

**Parameters:**
1. `{{1}}` - App/Company name (e.g., "AliranTunai")
2. `{{2}}` - OTP code (6 digits)
3. `{{3}}` - Expiry time (e.g., "5")

**Footer:** (Optional)
```
AliranTunai - Cash Flow Management
```

**Buttons:** (Optional but recommended)
- Type: **Copy Code**
- Button text: "Copy Code"
- Code type: **One-Time Password**
- Package name: Leave empty (for web apps)

### Example Message Preview
```
Your AliranTunai verification code is *123456*.

This code expires in 5 minutes. Do not share this code with anyone.
```

## Step 3: Submit for Approval

1. Click **Submit**
2. Wait for Meta approval (usually within a few hours)
3. You'll receive an email when approved

## Step 4: Update Your Code (Already Done!)

The code has been updated to use the template:
- `send_whatsapp_otp()` function uses the template API
- No more 24-hour window restrictions
- OTPs will be delivered instantly

## Testing

After approval, test the OTP flow:

1. Try logging in from the frontend
2. Check server logs for template delivery status
3. Verify OTP is received on WhatsApp

## Troubleshooting

### Template Rejected
- Ensure the category is **AUTHENTICATION**
- Don't add marketing content
- Keep the message simple and clear

### Template Not Delivering
- Check WhatsApp Business Phone Number is verified
- Verify access token has correct permissions
- Check template name matches exactly: `otp_login`

### Need Multiple Languages?
Create the same template for each language:
- `otp_login` (English)
- `otp_login_ms` (Malay) - if needed
- Update the code to detect user language preference

## Template API Format

The code sends templates like this:
```json
{
  "messaging_product": "whatsapp",
  "to": "60123456789",
  "type": "template",
  "template": {
    "name": "otp_login",
    "language": { "code": "en" },
    "components": [
      {
        "type": "body",
        "parameters": [
          { "type": "text", "text": "AliranTunai" },
          { "type": "text", "text": "123456" },
          { "type": "text", "text": "5" }
        ]
      }
    ]
  }
}
```

## Benefits

✅ No 24-hour messaging window required  
✅ Free authentication messages (no cost)  
✅ Instant delivery  
✅ Professional appearance  
✅ Copy code button for better UX  
✅ Compliant with WhatsApp policies  

## Next Steps

1. Create the template in Meta Business Suite
2. Wait for approval
3. Test the login flow
4. Monitor delivery success rates

For more info: https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates
