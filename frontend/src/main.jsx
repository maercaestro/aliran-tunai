import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import PrivacyPolicy from './PrivacyPolicy.jsx'
import BrandPreview from './pages/BrandPreview.jsx'
import Dashboard from './pages/Dashboard.jsx'
import WorkOrderDetail from './pages/WorkOrderDetail.jsx'
import { AuthProvider } from './contexts/AuthContext'
import brandConfig, { getCSSVariables } from './config/brand'

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
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/work-order/:orderId" element={<WorkOrderDetail />} />
          <Route path="/login" element={<Navigate to="/dashboard" replace />} />
          <Route path="/privacy-policy" element={<PrivacyPolicy />} />
          <Route path="/brand-preview" element={<BrandPreview />} />
        </Routes>
      </Router>
    </AuthProvider>
  </StrictMode>,
)
