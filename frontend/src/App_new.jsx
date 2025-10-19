import { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import './App.css'

// Import existing B2B components (preserved)
import Login from './components/Login'
import AddTransactionModal from './components/AddTransactionModal'
import SettingsModal from './components/SettingsModal'
import HelpModal from './components/HelpModal'
import ReportsPage from './components/ReportsPage'

// New components for personal budget
import ModeSelector from './components/ModeSelector'
import PersonalDashboard from './components/personal/PersonalDashboard'
import PersonalExpenses from './components/personal/PersonalExpenses'  
import PersonalBudgets from './components/personal/PersonalBudgets'
import PersonalGoals from './components/personal/PersonalGoals'
import PersonalInsights from './components/personal/PersonalInsights'
import BusinessDashboard from './components/business/BusinessDashboard'

import { buildApiUrl, API_ENDPOINTS } from './config/api'

function App() {
  // Authentication state (shared between modes)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [authToken, setAuthToken] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  
  // App mode state
  const [appMode, setAppMode] = useState('personal') // 'personal' | 'business'
  
  const navigate = useNavigate()

  // Check authentication on app load
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('auth_token')
      const userInfo = localStorage.getItem('user_info')
      const savedMode = localStorage.getItem('app_mode') || 'personal'
      
      if (token && userInfo) {
        try {
          const parsedUser = JSON.parse(userInfo)
          setUser(parsedUser)
          setAuthToken(token)
          setIsAuthenticated(true)
          setAppMode(savedMode)
        } catch (error) {
          console.error('Error parsing user info:', error)
          logout()
        }
      }
      setAuthLoading(false)
    }

    checkAuth()
  }, [])

  // Handle successful login
  const handleLoginSuccess = (userData, token) => {
    setUser(userData)
    setAuthToken(token)
    setIsAuthenticated(true)
    
    // Store auth data
    localStorage.setItem('auth_token', token)
    localStorage.setItem('user_info', JSON.stringify(userData))
    
    // Redirect based on current mode
    if (appMode === 'business') {
      navigate('/business')
    } else {
      navigate('/personal')
    }
  }

  // Handle logout
  const logout = () => {
    setIsAuthenticated(false)
    setUser(null)
    setAuthToken(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_info')
    navigate('/')
  }

  // Handle mode change
  const handleModeChange = (newMode) => {
    setAppMode(newMode)
    localStorage.setItem('app_mode', newMode)
    
    if (newMode === 'business') {
      navigate('/business')
    } else {
      navigate('/personal')
    }
  }

  // Loading state during auth check
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="App">
      <Routes>
        {/* Landing page with mode selection */}
        <Route 
          path="/" 
          element={
            isAuthenticated ? 
              <Navigate to={appMode === 'business' ? '/business' : '/personal'} replace /> :
              <ModeSelector onModeSelect={handleModeChange} selectedMode={appMode} />
          } 
        />
        
        {/* Login route */}
        <Route 
          path="/login" 
          element={
            isAuthenticated ? 
              <Navigate to={appMode === 'business' ? '/business' : '/personal'} replace /> :
              <Login onLoginSuccess={handleLoginSuccess} mode={appMode} />
          } 
        />

        {/* Business (B2B) Routes - Preserved */}
        <Route path="/business/*" element={
          <ProtectedBusinessRoutes 
            isAuthenticated={isAuthenticated}
            user={user}
            authToken={authToken}
            onLogout={logout}
            onModeChange={handleModeChange}
          />
        } />

        {/* Personal Budget Routes - New */}
        <Route path="/personal/*" element={
          <ProtectedPersonalRoutes 
            isAuthenticated={isAuthenticated}
            user={user}
            authToken={authToken}
            onLogout={logout}
            onModeChange={handleModeChange}
          />
        } />

        {/* Fallback redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

// Protected Business Routes Component
function ProtectedBusinessRoutes({ isAuthenticated, user, authToken, onLogout, onModeChange }) {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <Routes>
      <Route path="/" element={
        <BusinessDashboard 
          user={user} 
          authToken={authToken}
          onLogout={onLogout}
          onModeChange={onModeChange}
        />
      } />
      <Route path="/reports" element={
        <ReportsPage 
          user={user}
          authToken={authToken}
          onLogout={onLogout}
          onModeChange={onModeChange}
        />
      } />
    </Routes>
  )
}

// Protected Personal Routes Component  
function ProtectedPersonalRoutes({ isAuthenticated, user, authToken, onLogout, onModeChange }) {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <Routes>
      <Route path="/" element={
        <PersonalDashboard 
          user={user}
          authToken={authToken}
          onLogout={onLogout}
          onModeChange={onModeChange}
        />
      } />
      <Route path="/expenses" element={
        <PersonalExpenses 
          user={user}
          authToken={authToken}
          onLogout={onLogout}
          onModeChange={onModeChange}
        />
      } />
      <Route path="/budgets" element={
        <PersonalBudgets 
          user={user}
          authToken={authToken}
          onLogout={onLogout}
          onModeChange={onModeChange}
        />
      } />
      <Route path="/goals" element={
        <PersonalGoals 
          user={user}
          authToken={authToken}
          onLogout={onLogout}
          onModeChange={onModeChange}
        />
      } />
      <Route path="/insights" element={
        <PersonalInsights 
          user={user}
          authToken={authToken}
          onLogout={onLogout}
          onModeChange={onModeChange}
        />
      } />
    </Routes>
  )
}

export default App