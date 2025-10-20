import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './index.css'
import AppRouter from './AppRouter.jsx'  // New routing structure with personal budget support
import PrivacyPolicy from './PrivacyPolicy.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Router>
      <Routes>
        {/* New routing structure with personal budget support */}
        <Route path="/*" element={<AppRouter />} />
        
        {/* Privacy policy */}
        <Route path="/privacy-policy" element={<PrivacyPolicy />} />
      </Routes>
    </Router>
  </StrictMode>,
)
