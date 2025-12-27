// API Configuration
const isDevelopment = import.meta.env.DEV
const isProduction = import.meta.env.PROD

// Base URL for API calls
export const API_BASE_URL = isDevelopment 
  ? '' // Use proxy in development (empty string for relative URLs)
  : 'https://api.aliran-tunai.com' // Production API URL

// Helper function to build API URLs
export const buildApiUrl = (endpoint) => {
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint
  return `${API_BASE_URL}/${cleanEndpoint}`
}

// API endpoints
export const API_ENDPOINTS = {
  // Auth endpoints
  SEND_OTP: '/api/auth/send-otp',
  VERIFY_OTP: '/api/auth/verify-otp',
  
  // Dashboard endpoints
  DASHBOARD: (userId) => `/api/dashboard/${userId}`,
  
  // Transaction endpoints
  TRANSACTIONS: '/api/transactions',
  USER_TRANSACTIONS: (userId) => `/api/transactions/${userId}`,
  TRANSACTION: (transactionId) => `/api/transactions/${transactionId}`,
  
  // Utility endpoints
  DOWNLOAD_EXCEL: (userId) => `/api/download-excel/${userId}`,
  HEALTH: '/api/health',
  USERS: '/api/users'
}