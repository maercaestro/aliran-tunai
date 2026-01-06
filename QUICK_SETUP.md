# Quick Reference: Vercel Environment Variables Setup

## For Aliran-Tunai Domain

Copy these to your **existing** Vercel project:

\`\`\`
VITE_API_URL=https://api.aliran-tunai.com
VITE_BRAND_NAME=Aliran-Tunai
VITE_BRAND_LOGO_PATH=/final-logo.png
VITE_BRAND_LOGO_ALT=Aliran Logo
VITE_BRAND_FAVICON=/final-logo.png
VITE_BRAND_COLOR_PRIMARY=#00F0B5
VITE_BRAND_COLOR_PRIMARY_HOVER=#00D9A3
VITE_BRAND_COLOR_SECONDARY=#2DD4BF
VITE_BRAND_META_TITLE=Aliran-Tunai
\`\`\`

---

## For New Brand Domain

Copy these to your **new** Vercel project, then customize the values:

\`\`\`
VITE_API_URL=https://api.aliran-tunai.com
VITE_BRAND_NAME=YourNewBrandName
VITE_BRAND_LOGO_PATH=/yournewbrand-logo.png
VITE_BRAND_LOGO_ALT=YourNewBrand Logo
VITE_BRAND_FAVICON=/yournewbrand-favicon.png
VITE_BRAND_COLOR_PRIMARY=#3B82F6
VITE_BRAND_COLOR_PRIMARY_HOVER=#2563EB
VITE_BRAND_COLOR_SECONDARY=#8B5CF6
VITE_BRAND_META_TITLE=YourNewBrand
\`\`\`

**Remember to:**
1. Upload your new logo to `/frontend/public/` folder
2. Commit and push to GitHub
3. Redeploy both Vercel projects

---

## Steps to Deploy New Brand

1. **Upload Logo**: Add your logo file to `frontend/public/` (e.g., `newbrand-logo.png`)
2. **Create Vercel Project**: Go to vercel.com → New Project → Import your GitHub repo
3. **Configure Settings**:
   - Root Directory: `frontend`
   - Framework: `Vite`
4. **Add Environment Variables**: Copy the variables above and customize
5. **Deploy**: Click "Deploy"
6. **Add Domain**: Go to Settings → Domains → Add your new domain

Done! 🎉
