/**
 * Feature Flag Configuration
 * Enables switching between B2B and Personal Budget modes
 */

// Environment-based feature flags
const FEATURE_FLAGS = {
  // App mode features
  PERSONAL_BUDGET_MODE: process.env.REACT_APP_ENABLE_PERSONAL_BUDGET !== 'false',
  BUSINESS_MODE: process.env.REACT_APP_ENABLE_BUSINESS !== 'false',
  
  // Mode switching
  ALLOW_MODE_SWITCHING: process.env.REACT_APP_ALLOW_MODE_SWITCHING !== 'false',
  
  // Default mode (can be overridden by user preference)
  DEFAULT_MODE: process.env.REACT_APP_DEFAULT_MODE || 'personal', // 'personal' | 'business'
  
  // Development features
  SHOW_DEBUG_INFO: process.env.NODE_ENV === 'development',
  LEGACY_MODE_ACCESS: process.env.NODE_ENV === 'development',
  
  // Personal budget features (can be enabled gradually)
  PERSONAL_DASHBOARD: true,
  PERSONAL_EXPENSES: process.env.REACT_APP_ENABLE_EXPENSES !== 'false',
  PERSONAL_BUDGETS: process.env.REACT_APP_ENABLE_BUDGETS !== 'false',
  PERSONAL_GOALS: process.env.REACT_APP_ENABLE_GOALS !== 'false',
  PERSONAL_INSIGHTS: process.env.REACT_APP_ENABLE_INSIGHTS !== 'false',
  
  // WhatsApp bot adaptations
  PERSONAL_BOT_RESPONSES: process.env.REACT_APP_ENABLE_PERSONAL_BOT !== 'false',
  BUSINESS_BOT_RESPONSES: process.env.REACT_APP_ENABLE_BUSINESS_BOT !== 'false',
}

/**
 * Check if a feature is enabled
 * @param {string} featureName - Name of the feature flag
 * @returns {boolean} - Whether the feature is enabled
 */
export function isFeatureEnabled(featureName) {
  return FEATURE_FLAGS[featureName] === true
}

/**
 * Get the default app mode based on feature flags
 * @returns {string} - 'personal' or 'business'
 */
export function getDefaultMode() {
  if (!isFeatureEnabled('PERSONAL_BUDGET_MODE')) {
    return 'business'
  }
  if (!isFeatureEnabled('BUSINESS_MODE')) {
    return 'personal'
  }
  return FEATURE_FLAGS.DEFAULT_MODE
}

/**
 * Check if mode switching is allowed
 * @returns {boolean}
 */
export function canSwitchModes() {
  return isFeatureEnabled('ALLOW_MODE_SWITCHING') && 
         isFeatureEnabled('PERSONAL_BUDGET_MODE') && 
         isFeatureEnabled('BUSINESS_MODE')
}

/**
 * Get available app modes
 * @returns {Array<string>} - Array of available modes
 */
export function getAvailableModes() {
  const modes = []
  if (isFeatureEnabled('PERSONAL_BUDGET_MODE')) {
    modes.push('personal')
  }
  if (isFeatureEnabled('BUSINESS_MODE')) {
    modes.push('business')
  }
  return modes
}

/**
 * Development helper to show feature flag status
 */
export function getFeatureFlagStatus() {
  if (!isFeatureEnabled('SHOW_DEBUG_INFO')) {
    return null
  }
  
  return {
    ...FEATURE_FLAGS,
    availableModes: getAvailableModes(),
    defaultMode: getDefaultMode(),
    canSwitchModes: canSwitchModes()
  }
}

// Export the raw flags for direct access if needed
export { FEATURE_FLAGS }

export default {
  isFeatureEnabled,
  getDefaultMode,
  canSwitchModes,
  getAvailableModes,
  getFeatureFlagStatus,
  FEATURE_FLAGS
}