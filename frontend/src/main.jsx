import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.jsx'
import PrivacyPolicy from './PrivacyPolicy.jsx'
import BrandPreview from './pages/BrandPreview.jsx'
import LandingPage from './pages/LandingPage.jsx'
import LoginPage from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Transactions from './pages/Transactions.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import { AuthProvider } from './contexts/AuthContext.jsx'
import brandConfig, { getCSSVariables } from './config/brand'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// Apply brand configuration to document
document.title = brandConfig.meta.title
document.querySelector('#favicon')?.setAttribute('href', brandConfig.favicon)
document.querySelector('#meta-description')?.setAttribute('content', brandConfig.meta.description)
document.querySelector('#meta-keywords')?.setAttribute('content', brandConfig.meta.keywords)

// Apply CSS variables for theming
const root = document.documentElement
Object.entries(getCSSVariables()).forEach(([key, value]) => {
  root.style.setProperty(key, value)
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <Router>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<App />} />
            <Route path="/landing" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/transactions" element={<ProtectedRoute><Transactions /></ProtectedRoute>} />
            <Route path="/privacy-policy" element={<PrivacyPolicy />} />
            <Route path="/brand-preview" element={<BrandPreview />} />
          </Routes>
        </AuthProvider>
      </Router>
    </QueryClientProvider>
  </StrictMode>,
)
