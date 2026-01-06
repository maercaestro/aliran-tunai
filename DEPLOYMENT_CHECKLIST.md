# Multi-Brand Deployment Checklist

Use this checklist when setting up your new brand domain.

## Pre-Deployment Checklist

### 1. Brand Assets Ready ☐
- [ ] New logo file created (PNG with transparency recommended)
- [ ] Logo uploaded to `frontend/public/` folder
- [ ] Favicon created (or using same logo)
- [ ] Logo filename noted (e.g., `newbrand-logo.png`)

### 2. Brand Identity Defined ☐
- [ ] Brand name decided
- [ ] Primary color chosen (hex code)
- [ ] Secondary color chosen (hex code)
- [ ] Color scheme tested (use brand preview page)

### 3. Code Committed ☐
- [ ] Logo files added to git
- [ ] Changes committed to GitHub
- [ ] Changes pushed to remote repository

## Vercel Deployment Checklist

### For Existing Brand (Aliran-Tunai)

- [ ] Logged into Vercel
- [ ] Opened existing project settings
- [ ] Added environment variables (see QUICK_SETUP.md)
- [ ] Redeployed project
- [ ] Verified deployment successful
- [ ] Tested website at domain

### For New Brand

#### Step 1: Create Vercel Project
- [ ] Went to https://vercel.com/new
- [ ] Clicked "Import Project"
- [ ] Selected GitHub repository
- [ ] Named project (e.g., "newbrand-frontend")

#### Step 2: Configure Build Settings
- [ ] Set Framework Preset: `Vite`
- [ ] Set Root Directory: `frontend`
- [ ] Set Build Command: `npm run build` (should be auto-detected)
- [ ] Set Output Directory: `dist` (should be auto-detected)

#### Step 3: Environment Variables
Copy from QUICK_SETUP.md and customize:

- [ ] `VITE_API_URL` (set to your API)
- [ ] `VITE_BRAND_NAME` (your brand name)
- [ ] `VITE_BRAND_LOGO_PATH` (e.g., `/newbrand-logo.png`)
- [ ] `VITE_BRAND_LOGO_ALT` (e.g., "NewBrand Logo")
- [ ] `VITE_BRAND_FAVICON` (your favicon path)
- [ ] `VITE_BRAND_COLOR_PRIMARY` (your primary color)
- [ ] `VITE_BRAND_COLOR_PRIMARY_HOVER` (slightly darker primary)
- [ ] `VITE_BRAND_COLOR_SECONDARY` (your secondary color)
- [ ] `VITE_BRAND_META_TITLE` (browser title)
- [ ] `VITE_BRAND_META_DESCRIPTION` (SEO description)
- [ ] `VITE_BRAND_META_KEYWORDS` (SEO keywords)

Optional variables (use defaults if not needed):
- [ ] `VITE_BRAND_BG_GRADIENT_FROM`
- [ ] `VITE_BRAND_BG_GRADIENT_TO`
- [ ] `VITE_BRAND_TEXT_PRIMARY`
- [ ] `VITE_BRAND_TEXT_SECONDARY`
- [ ] `VITE_BRAND_CARD_BG`
- [ ] `VITE_BRAND_CARD_BG_HOVER`

#### Step 4: Deploy
- [ ] Clicked "Deploy" button
- [ ] Waited for build to complete
- [ ] Checked deployment logs for errors
- [ ] Verified no build errors

#### Step 5: Add Custom Domain
- [ ] Went to Project Settings → Domains
- [ ] Clicked "Add Domain"
- [ ] Entered new domain name
- [ ] Followed DNS configuration instructions
- [ ] Waited for DNS propagation (can take up to 48 hours)

## Post-Deployment Verification

### Test New Brand Website
- [ ] Website loads at new domain
- [ ] Logo displays correctly
- [ ] Colors match brand guidelines
- [ ] Page title correct in browser tab
- [ ] Favicon displays correctly
- [ ] Login functionality works
- [ ] Dashboard loads properly
- [ ] All features work as expected

### Test Brand Preview Page
- [ ] Visit `/brand-preview` on new domain
- [ ] Verify logo displays
- [ ] Check all colors render correctly
- [ ] Confirm environment variables are set (should show green)
- [ ] Compare with design requirements

### Browser Testing
- [ ] Test in Chrome
- [ ] Test in Safari
- [ ] Test in Firefox
- [ ] Test on mobile device
- [ ] Clear cache and retest

## Common Issues & Solutions

### Logo not showing
- [ ] Confirmed logo file exists in `frontend/public/`
- [ ] Verified `VITE_BRAND_LOGO_PATH` starts with `/`
- [ ] Checked filename matches exactly (case-sensitive)
- [ ] Cleared browser cache
- [ ] Redeployed project

### Colors not applying
- [ ] Verified all color values are valid hex codes (with #)
- [ ] Checked environment variables are set in Vercel
- [ ] Redeployed after setting variables
- [ ] Hard refreshed browser (Cmd+Shift+R / Ctrl+Shift+F5)

### Build failures
- [ ] Checked Vercel deployment logs
- [ ] Verified all environment variables set correctly
- [ ] Ensured no syntax errors in brand config
- [ ] Tested build locally: `cd frontend && npm run build`

### Domain not working
- [ ] Confirmed DNS records added correctly
- [ ] Waited for DNS propagation (up to 48 hours)
- [ ] Checked Vercel domain status
- [ ] Tried accessing via HTTPS

## Maintenance Checklist

### When Adding Features
- [ ] Test on both brands
- [ ] Ensure no hardcoded brand-specific values
- [ ] Use `brandConfig` for any brand-dependent logic

### When Fixing Bugs
- [ ] Fix in main codebase
- [ ] Deploy to all brand projects
- [ ] Verify fix on all domains

### When Updating Branding
- [ ] Update environment variables in Vercel
- [ ] Redeploy project
- [ ] Clear CDN cache if applicable
- [ ] Verify changes on live site

---

## Quick Reference Links

- **Full Documentation**: [MULTI_BRAND_DEPLOYMENT.md](MULTI_BRAND_DEPLOYMENT.md)
- **Environment Variables**: [QUICK_SETUP.md](QUICK_SETUP.md)
- **Implementation Summary**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Brand Config File**: `frontend/src/config/brand.js`

---

**Status**: Ready for deployment ✅

**Last Updated**: January 5, 2026
