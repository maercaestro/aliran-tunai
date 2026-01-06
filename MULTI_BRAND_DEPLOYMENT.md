# Multi-Brand Deployment Guide

This guide explains how to deploy your application to multiple domains with different branding using the same codebase.

## Overview

Your frontend is now configured to support multiple brands through environment variables. This means:
- ✅ Single codebase to maintain
- ✅ Deploy to multiple domains with different branding
- ✅ Easy to add more brands in the future
- ✅ Each brand can have its own logo, colors, and name

## Setup Instructions

### 1. Prepare Your Brand Assets

For **each brand**, prepare the following:

1. **Logo file** (PNG recommended, with transparency)
   - Add to `/frontend/public/` folder
   - Example: `newbrand-logo.png`

2. **Favicon** (optional, can use same as logo)
   - Also in `/frontend/public/`
   - Example: `newbrand-favicon.png`

3. **Brand colors** (Hex format)
   - Primary color
   - Secondary color
   - Background colors
   - Text colors

### 2. Configure Environment Variables

#### For Aliran-Tunai (Current Brand)

In Vercel project settings, add these environment variables:

\`\`\`env
VITE_API_URL=https://api.aliran-tunai.com
VITE_BRAND_NAME=Aliran-Tunai
VITE_BRAND_LOGO_PATH=/final-logo.png
VITE_BRAND_LOGO_ALT=Aliran Logo
VITE_BRAND_FAVICON=/final-logo.png
VITE_BRAND_COLOR_PRIMARY=#00F0B5
VITE_BRAND_COLOR_PRIMARY_HOVER=#00D9A3
VITE_BRAND_COLOR_SECONDARY=#2DD4BF
VITE_BRAND_BG_GRADIENT_FROM=#030711
VITE_BRAND_BG_GRADIENT_TO=#0f172a
VITE_BRAND_TEXT_PRIMARY=#ffffff
VITE_BRAND_TEXT_SECONDARY=#94a3b8
VITE_BRAND_CARD_BG=#1e293b
VITE_BRAND_CARD_BG_HOVER=#334155
VITE_BRAND_META_TITLE=Aliran-Tunai
VITE_BRAND_META_DESCRIPTION=Smart financial management platform for businesses and individuals
VITE_BRAND_META_KEYWORDS=accounting, finance, erp, cash flow
\`\`\`

#### For New Brand

In **new** Vercel project settings, add these environment variables (CUSTOMIZE VALUES):

\`\`\`env
VITE_API_URL=https://api.aliran-tunai.com
VITE_BRAND_NAME=YourNewBrand
VITE_BRAND_LOGO_PATH=/newbrand-logo.png
VITE_BRAND_LOGO_ALT=YourNewBrand Logo
VITE_BRAND_FAVICON=/newbrand-favicon.png
VITE_BRAND_COLOR_PRIMARY=#3B82F6
VITE_BRAND_COLOR_PRIMARY_HOVER=#2563EB
VITE_BRAND_COLOR_SECONDARY=#8B5CF6
VITE_BRAND_BG_GRADIENT_FROM=#0a0a0a
VITE_BRAND_BG_GRADIENT_TO=#1a1a2e
VITE_BRAND_TEXT_PRIMARY=#ffffff
VITE_BRAND_TEXT_SECONDARY=#a1a1aa
VITE_BRAND_CARD_BG=#27272a
VITE_BRAND_CARD_BG_HOVER=#3f3f46
VITE_BRAND_META_TITLE=YourNewBrand - Financial Management
VITE_BRAND_META_DESCRIPTION=Modern financial management solution
VITE_BRAND_META_KEYWORDS=finance, accounting, business management
\`\`\`

### 3. Deploy to Vercel

#### Option A: Two Separate Vercel Projects (Recommended)

1. **First Project (Aliran-Tunai)**
   - Connect to your GitHub repository
   - Set root directory: `frontend`
   - Add environment variables (Aliran-Tunai values)
   - Connect to domain: `aliran-tunai.com`

2. **Second Project (New Brand)**
   - Create NEW Vercel project
   - Connect to the SAME GitHub repository
   - Set root directory: `frontend`
   - Add environment variables (New Brand values)
   - Connect to domain: `yournewdomain.com`

#### Option B: Use Vercel Preview Deployments

1. Create a new branch: `brand-newbrand`
2. Configure environment variables per branch in Vercel
3. Connect different domains to different branches

### 4. Vercel Deployment Steps

For each brand:

1. **Create New Project in Vercel**
   - Go to https://vercel.com/new
   - Import your GitHub repository
   - Click "Import"

2. **Configure Build Settings**
   - Framework Preset: `Vite`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Add Environment Variables**
   - Go to Project Settings → Environment Variables
   - Add all the `VITE_*` variables from above
   - Make sure to customize for each brand!

4. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete

5. **Add Custom Domain**
   - Go to Project Settings → Domains
   - Add your domain (e.g., `yournewdomain.com`)
   - Follow Vercel's DNS configuration instructions

## Color Scheme Picker

Here are some popular color schemes you can use for your new brand:

### Modern Blue
\`\`\`
Primary: #3B82F6
Primary Hover: #2563EB
Secondary: #8B5CF6
\`\`\`

### Vibrant Purple
\`\`\`
Primary: #A855F7
Primary Hover: #9333EA
Secondary: #EC4899
\`\`\`

### Professional Green
\`\`\`
Primary: #10B981
Primary Hover: #059669
Secondary: #14B8A6
\`\`\`

### Bold Orange
\`\`\`
Primary: #F97316
Primary Hover: #EA580C
Secondary: #FB923C
\`\`\`

## Testing Locally

To test different brands locally:

1. **Create `.env.local` file** in `/frontend` folder:
   \`\`\`env
   VITE_BRAND_NAME=TestBrand
   VITE_BRAND_LOGO_PATH=/test-logo.png
   # ... other variables
   \`\`\`

2. **Run development server:**
   \`\`\`bash
   cd frontend
   npm run dev
   \`\`\`

3. **Switch brands** by changing `.env.local` and restarting server

## Troubleshooting

### Logo not showing
- Check the logo file is in `/frontend/public/` folder
- Verify `VITE_BRAND_LOGO_PATH` starts with `/`
- Clear browser cache

### Colors not applying
- Ensure all color values are valid Hex codes (starting with #)
- Check environment variables are set in Vercel
- Redeploy after changing environment variables

### Title/Meta not updating
- Environment variables only apply at build time
- Need to redeploy after changing them
- Check browser cache and refresh

## Advanced: Adding More Customization

You can extend the brand configuration by editing:
- `/frontend/src/config/brand.js` - Add more brand properties
- `/frontend/src/main.jsx` - Apply additional CSS variables
- `/frontend/src/App.jsx` - Use brand config in more places

## Summary

✅ Same codebase, multiple brands
✅ Configure via environment variables
✅ Deploy to different domains
✅ Easy to maintain and update

For questions or issues, refer to the configuration files:
- `/frontend/src/config/brand.js` - Brand configuration logic
- `/frontend/.env.example` - Default brand example
- `/frontend/.env.newbrand.example` - New brand example
