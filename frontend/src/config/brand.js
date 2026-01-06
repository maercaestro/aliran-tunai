/**
 * Brand Configuration
 * 
 * This file reads brand-specific settings from environment variables.
 * Different brands can be deployed from the same codebase by setting
 * different environment variables in Vercel/deployment platform.
 */

const brandConfig = {
  // Brand Name
  name: import.meta.env.VITE_BRAND_NAME || 'Aliran-Tunai',
  
  // Logo Settings
  logo: {
    // Path to logo in /public folder
    path: import.meta.env.VITE_BRAND_LOGO_PATH || '/final-logo.png',
    alt: import.meta.env.VITE_BRAND_LOGO_ALT || 'Aliran Logo',
  },
  
  // Favicon
  favicon: import.meta.env.VITE_BRAND_FAVICON || '/final-logo.png',
  
  // Color Scheme (CSS variables or Tailwind classes)
  colors: {
    // Primary brand color (used for buttons, highlights, etc.)
    primary: import.meta.env.VITE_BRAND_COLOR_PRIMARY || '#00F0B5',
    primaryHover: import.meta.env.VITE_BRAND_COLOR_PRIMARY_HOVER || '#00D9A3',
    
    // Secondary/accent color
    secondary: import.meta.env.VITE_BRAND_COLOR_SECONDARY || '#2DD4BF',
    
    // Background gradient
    backgroundGradientFrom: import.meta.env.VITE_BRAND_BG_GRADIENT_FROM || '#030711',
    backgroundGradientTo: import.meta.env.VITE_BRAND_BG_GRADIENT_TO || '#0f172a',
    
    // Text colors
    textPrimary: import.meta.env.VITE_BRAND_TEXT_PRIMARY || '#ffffff',
    textSecondary: import.meta.env.VITE_BRAND_TEXT_SECONDARY || '#94a3b8',
    
    // Card/container background
    cardBackground: import.meta.env.VITE_BRAND_CARD_BG || '#1e293b',
    cardBackgroundHover: import.meta.env.VITE_BRAND_CARD_BG_HOVER || '#334155',
  },
  
  // Meta Information
  meta: {
    title: import.meta.env.VITE_BRAND_META_TITLE || 'Aliran-Tunai',
    description: import.meta.env.VITE_BRAND_META_DESCRIPTION || 
      'Smart financial management platform for businesses and individuals',
    keywords: import.meta.env.VITE_BRAND_META_KEYWORDS || 
      'accounting, finance, erp, cash flow',
  },
  
  // Social/External Links
  social: {
    facebook: import.meta.env.VITE_BRAND_FACEBOOK || '',
    twitter: import.meta.env.VITE_BRAND_TWITTER || '',
    instagram: import.meta.env.VITE_BRAND_INSTAGRAM || '',
  },
  
  // Feature Flags (if brands have different features)
  features: {
    showReports: import.meta.env.VITE_FEATURE_REPORTS !== 'false',
    showSettings: import.meta.env.VITE_FEATURE_SETTINGS !== 'false',
    showHelp: import.meta.env.VITE_FEATURE_HELP !== 'false',
  }
}

export default brandConfig

// Helper function to get CSS custom properties
export const getCSSVariables = () => {
  return {
    '--brand-primary': brandConfig.colors.primary,
    '--brand-primary-hover': brandConfig.colors.primaryHover,
    '--brand-secondary': brandConfig.colors.secondary,
    '--brand-bg-from': brandConfig.colors.backgroundGradientFrom,
    '--brand-bg-to': brandConfig.colors.backgroundGradientTo,
    '--brand-text-primary': brandConfig.colors.textPrimary,
    '--brand-text-secondary': brandConfig.colors.textSecondary,
    '--brand-card-bg': brandConfig.colors.cardBackground,
    '--brand-card-bg-hover': brandConfig.colors.cardBackgroundHover,
  }
}
