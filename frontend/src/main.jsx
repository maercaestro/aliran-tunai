import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './index.css'
import App from './App_new.jsx'  // Using the new routing structure
import AppOld from './App.jsx'   // Preserve old app for reference
import PrivacyPolicy from './PrivacyPolicy.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Router>
      <Routes>
        {/* New routing structure with mode selection */}
        <Route path="/*" element={<App />} />
        
        {/* Direct access to old B2B app (for development/fallback) */}
        <Route path="/legacy/*" element={<AppOld />} />
        
        {/* Privacy policy */}
        <Route path="/privacy-policy" element={<PrivacyPolicy />} />
      </Routes>
    </Router>
  </StrictMode>,
)
