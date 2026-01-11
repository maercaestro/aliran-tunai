import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import './App.css'

function App() {
  const navigate = useNavigate()
  const { isAuthenticated, loading } = useAuth()

  useEffect(() => {
    if (!loading) {
      // Check if user has visited before
      const hasVisited = localStorage.getItem('visited_before')
      
      if (!hasVisited) {
        // First time visitor - show landing page
        navigate('/landing', { replace: true })
      } else if (isAuthenticated) {
        // Returning user with auth - go to dashboard
        navigate('/dashboard', { replace: true })
      } else {
        // Returning user without auth - go to login
        navigate('/login', { replace: true })
      }
    }
  }, [loading, isAuthenticated, navigate])

  // Show loading state while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A192F] flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-[#00F0B5]"></div>
          <p className="mt-4 text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  return null
}

export default App
