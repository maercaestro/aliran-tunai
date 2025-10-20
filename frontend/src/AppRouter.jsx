import { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import './App.css'

// Import existing components
import Login from './components/Login'
import ModeSelector from './components/ModeSelector'
import PersonalDashboard from './components/PersonalDashboard'
import ReportsPage from './components/ReportsPage'
import { buildApiUrl, API_ENDPOINTS } from './config/api'

function AppRouter() {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [authToken, setAuthToken] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  
  // App mode state
  const [appMode, setAppMode] = useState(() => {
    return localStorage.getItem('aliran_mode') || 
           import.meta.env.REACT_APP_DEFAULT_MODE || 
           'personal'
  })

  // Check authentication on app load
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('auth_token')
      const userInfo = localStorage.getItem('user_info')
      
      if (token && userInfo) {
        try {
          const parsedUser = JSON.parse(userInfo)
          setUser(parsedUser)
          setAuthToken(token)
          setIsAuthenticated(true)
        } catch (error) {
          console.error('Error parsing user info:', error)
          clearAuth()
        }
      }
      setAuthLoading(false)
    }

    checkAuth()
  }, [])

  const clearAuth = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_info')
    setUser(null)
    setAuthToken(null)
    setIsAuthenticated(false)
  }

  const handleLogin = (userData, token) => {
    setUser(userData)
    setAuthToken(token)
    setIsAuthenticated(true)
    localStorage.setItem('auth_token', token)
    localStorage.setItem('user_info', JSON.stringify(userData))
  }

  const handleLogout = () => {
    clearAuth()
  }

  const handleModeChange = (newMode) => {
    setAppMode(newMode)
    localStorage.setItem('aliran_mode', newMode)
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2">Loading...</span>
      </div>
    )
  }

  // Feature flag checks
  const enablePersonal = import.meta.env.REACT_APP_ENABLE_PERSONAL_BUDGET !== 'false'
  const enableBusiness = import.meta.env.REACT_APP_ENABLE_BUSINESS !== 'false'

  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        {/* Mode Selection Route */}
        <Route 
          path="/" 
          element={
            <ModeSelector 
              onModeSelect={handleModeChange}
              selectedMode={appMode}
              isAuthenticated={isAuthenticated}
              user={user}
            />
          } 
        />

        {/* Login Route */}
        <Route 
          path="/login" 
          element={
            !isAuthenticated ? (
              <Login onLogin={handleLogin} mode={appMode} />
            ) : (
              <Navigate to={`/${appMode}/dashboard`} replace />
            )
          } 
        />

        {/* Personal Budget Routes */}
        {enablePersonal && (
          <Route path="/personal/*" element={
            <PersonalRoutes 
              isAuthenticated={isAuthenticated}
              user={user}
              authToken={authToken}
              onLogout={handleLogout}
              onModeChange={handleModeChange}
              currentMode={appMode}
            />
          } />
        )}

        {/* Business Routes */}
        {enableBusiness && (
          <Route path="/business/*" element={
            <BusinessRoutes 
              isAuthenticated={isAuthenticated}
              user={user}
              authToken={authToken}
              onLogout={handleLogout}
              onModeChange={handleModeChange}
              currentMode={appMode}
            />
          } />
        )}

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

// Personal Budget Routes Component
function PersonalRoutes({ isAuthenticated, user, authToken, onLogout, onModeChange, currentMode }) {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <div>
      {/* Navigation Header */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">💰 Personal Budget</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">Hello, {user?.owner_name || user?.email}</span>
              <button
                onClick={onLogout}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route 
            path="dashboard" 
            element={<PersonalDashboard user={user} authToken={authToken} />} 
          />
          <Route 
            path="expenses" 
            element={<div className="text-center py-8">
              <h2 className="text-xl font-semibold">Expenses Coming Soon</h2>
              <p className="text-gray-600">This feature is under development.</p>
            </div>} 
          />
          <Route 
            path="budget" 
            element={<div className="text-center py-8">
              <h2 className="text-xl font-semibold">Budget Management Coming Soon</h2>
              <p className="text-gray-600">This feature is under development.</p>
            </div>} 
          />
          <Route path="*" element={<Navigate to="dashboard" replace />} />
        </Routes>
      </main>
    </div>
  )
}

// Business Routes Component
function BusinessRoutes({ isAuthenticated, user, authToken, onLogout, onModeChange, currentMode }) {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <div>
      {/* Navigation Header */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">🏢 Business Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">Hello, {user?.owner_name || user?.email}</span>
              <button
                onClick={onLogout}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route 
            path="dashboard" 
            element={<ReportsPage user={user} authToken={authToken} />} 
          />
          <Route path="*" element={<Navigate to="dashboard" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default AppRouter