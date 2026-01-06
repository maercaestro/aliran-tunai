import { useState, useEffect } from 'react'
import './App.css'
import Login from './components/Login'
import AddTransactionModal from './components/AddTransactionModal'
import SettingsModal from './components/SettingsModal'
import HelpModal from './components/HelpModal'
import ReportsPage from './components/ReportsPage'
import { buildApiUrl, API_ENDPOINTS } from './config/api'
import brandConfig from './config/brand'

function App() {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [authToken, setAuthToken] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)

  // State for dashboard data
  const [dashboardData, setDashboardData] = useState({
    ccc: 0,
    dso: 0,
    dio: 0,
    dpo: 0,
    totalTransactions: 0,
    recentTransactions: [],
    summary: {
      totalSales: 0,
      totalPurchases: 0,
      totalPaymentsReceived: 0,
      totalPaymentsMade: 0
    }
  })

  // Personal budget data (for personal mode)
  const [personalData, setPersonalData] = useState({
    totalSpending: 1250,
    totalIncome: 5000,
    balance: 3750,
    categories: [
      { name: 'Food & Dining', amount: 450, transactions: 12, color: '#4CAF50' },
      { name: 'Transportation', amount: 300, transactions: 8, color: '#2196F3' },
      { name: 'Shopping', amount: 250, transactions: 5, color: '#FF9800' },
      { name: 'Entertainment', amount: 150, transactions: 3, color: '#9C27B0' },
      { name: 'Utilities', amount: 100, transactions: 2, color: '#F44336' }
    ],
    monthlySpending: [
      { month: 'October 2025', amount: 1250, transactions: 30 },
      { month: 'September 2025', amount: 1450, transactions: 28 },
      { month: 'August 2025', amount: 1100, transactions: 25 },
      { month: 'July 2025', amount: 1350, transactions: 32 }
    ],
    recentTransactions: [],
    totalTransactions: 0
  })

  // User mode detection
  const isPersonalMode = user?.mode === 'personal'
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  // Modal states
  const [addTransactionModalOpen, setAddTransactionModalOpen] = useState(false)
  const [settingsModalOpen, setSettingsModalOpen] = useState(false)
  const [helpModalOpen, setHelpModalOpen] = useState(false)
  
  // Page state
  const [currentPage, setCurrentPage] = useState('dashboard') // 'dashboard' or 'reports'

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
        } catch (err) {
          console.error('Error parsing user info:', err)
          logout()
        }
      }
      setAuthLoading(false)
    }
    
    checkAuth()
  }, [])

  // Handle successful login
  const handleLoginSuccess = (userData, token) => {
    console.log('handleLoginSuccess called with:', { userData, token: token ? `${token.substring(0, 20)}...` : null })
    setUser(userData)
    setAuthToken(token)
    setIsAuthenticated(true)
  }

  // Handle logout
  const logout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_phone')
    localStorage.removeItem('user_info')
    setUser(null)
    setAuthToken(null)
    setIsAuthenticated(false)
  }

  // Handle adding new transaction
  const handleAddTransaction = async (transactionData) => {
    try {
      const response = await fetch(buildApiUrl(API_ENDPOINTS.TRANSACTIONS), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(transactionData)
      })

      const data = await response.json()

      if (response.ok) {
        // Refresh dashboard data
        await fetchDashboardData()
      } else {
        throw new Error(data.error || 'Failed to add transaction')
      }
    } catch (err) {
      throw err
    }
  }

  // Handle user profile update
  const handleUserUpdate = (updatedUser) => {
    setUser(updatedUser)
    // Update localStorage
    localStorage.setItem('user_info', JSON.stringify(updatedUser))
  }

  // Download Excel function
  const downloadExcel = async () => {
    if (!user || !authToken) return
    
    try {
      const response = await fetch(buildApiUrl(API_ENDPOINTS.DOWNLOAD_EXCEL(user.wa_id)), {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })
      
      if (response.ok) {
        // Get the filename from the response headers or create a default one
        const contentDisposition = response.headers.get('content-disposition')
        let filename = `transactions_${user.company_name || user.wa_id}_${new Date().toISOString().slice(0, 10)}.xlsx`
        
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
          if (filenameMatch && filenameMatch[1]) {
            filename = filenameMatch[1].replace(/['"]/g, '')
          }
        }
        
        // Create blob and download
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        
        // Show success message (you could use a toast library for better UX)
        alert('Excel file downloaded successfully!')
      } else {
        const errorData = await response.json()
        alert(`Download failed: ${errorData.error || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Error downloading Excel:', err)
      alert('Failed to download Excel file. Please try again.')
    }
  }

  // Fetch dashboard data from API
  const fetchDashboardData = async () => {
    if (!user || !authToken) return
    
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(buildApiUrl(API_ENDPOINTS.DASHBOARD(user.wa_id)), {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })
      
      if (!response.ok) {
        if (response.status === 401) {
          logout()
          return
        }
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.error) {
        setError(data.error)
      } else {
        setDashboardData(data)
        setLastUpdated(new Date())
      }
      
    } catch (err) {
      console.error('Error fetching dashboard data:', err)
      setError(`Failed to load data: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  // Fetch personal budget data from API
  const fetchPersonalData = async () => {
    if (!user || !authToken) return
    
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(buildApiUrl(`/api/personal-budget/${user.wa_id}`), {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })
      
      if (!response.ok) {
        if (response.status === 401) {
          logout()
          return
        }
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.error) {
        setError(data.error)
      } else {
        setPersonalData(data)
        setLastUpdated(new Date())
      }
      
    } catch (err) {
      console.error('Error fetching personal data:', err)
      setError(`Failed to load personal budget data: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }
  
  // Effect to fetch data when authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      if (isPersonalMode) {
        fetchPersonalData()
      } else {
        fetchDashboardData()
      }
    }
  }, [isAuthenticated, user, isPersonalMode])

  const getCCCStatus = (ccc) => {
    if (ccc < 30) return { color: 'text-emerald-600', bg: 'from-emerald-50 to-emerald-100', status: 'Excellent', icon: '🎉' }
    if (ccc < 60) return { color: 'text-blue-600', bg: 'from-blue-50 to-blue-100', status: 'Good', icon: '👍' }
    if (ccc < 90) return { color: 'text-orange-600', bg: 'from-orange-50 to-orange-100', status: 'Moderate', icon: '⚠️' }
    return { color: 'text-red-600', bg: 'from-red-50 to-red-100', status: 'Needs Attention', icon: '🚨' }
  }

  const cccStatus = getCCCStatus(dashboardData.ccc)

  // Auth loading state
  if (authLoading) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center bg-[#0A192F]">
        <div className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#00F0B5] mx-auto mb-4"></div>
          <p className="text-white text-lg">Checking authentication...</p>
        </div>
      </div>
    )
  }

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  // Show reports page
  if (currentPage === 'reports') {
    return (
      <ReportsPage
        user={user}
        authToken={authToken}
        onBack={() => setCurrentPage('dashboard')}
      />
    )
  }

  // Loading state
  if (loading) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center bg-[#0A192F]">
        <div className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#00F0B5] mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading your financial dashboard...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center bg-[#0A192F]">
        <div className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-8 text-center max-w-md">
          <div className="text-red-400 text-6xl mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Connection Error</h2>
          <p className="text-[#B0B8C3] mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-6 py-3 bg-[#00F0B5] hover:bg-[#00D4A0] rounded-xl text-[#0A192F] font-medium transition-all"
          >
            Try Again
          </button>
          <div className="mt-4 p-3 bg-orange-500/10 border border-orange-500/30 rounded-xl">
            <p className="text-sm text-orange-400">
              <strong>Note:</strong> Make sure the API server is running on port 5001
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full min-h-screen relative bg-[#0A192F] text-[#B0B8C3] font-sans overflow-x-hidden">
      
      {/* Background Ambient Glow */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-[#00F0B5]/5 blur-[120px]"></div>
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[#2196F3]/5 blur-[120px]"></div>
        <div className="absolute top-1/2 left-1/6 transform -translate-y-1/2 opacity-[0.05] z-0">
          <img src={brandConfig.logo.path} alt="" className="w-[800px] h-auto object-contain" />
        </div>
      </div>
      
      {/* Header */}
      <header className="relative z-10 border-b border-white/5 bg-[#0A192F]/80 backdrop-blur-md sticky top-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <img src={brandConfig.logo.path} alt={brandConfig.logo.alt} className="h-10 w-auto drop-shadow-[0_0_10px_rgba(0,240,181,0.3)]" />
            </div>
            
            <div className="flex items-center space-x-6">
              {/* User Info */}
              <div className="text-right hidden sm:block">
                <div className="text-sm font-medium text-white">
                  {user?.owner_name || 'User'}
                </div>
                <div className="text-xs text-[#B0B8C3]">
                  {user?.company_name || `+${user?.wa_id}`}
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <button 
                  onClick={isPersonalMode ? fetchPersonalData : fetchDashboardData}
                  disabled={loading}
                  className="p-2 rounded-lg text-[#B0B8C3] hover:text-[#00F0B5] hover:bg-white/5 transition-colors"
                  title="Refresh Data"
                >
                  {loading ? <span className="animate-spin block"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg></span> : <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>}
                </button>
                
                <button 
                  onClick={downloadExcel}
                  disabled={loading || dashboardData.totalTransactions === 0}
                  className="flex items-center space-x-2 px-3 py-1.5 rounded-lg border border-white/10 text-sm text-[#B0B8C3] hover:border-[#00F0B5] hover:text-[#00F0B5] transition-all"
                  title="Download Excel"
                >
                  <span><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg></span>
                  <span className="hidden sm:inline">Export</span>
                </button>
                
                <button 
                  onClick={logout}
                  className="p-2 rounded-lg text-[#B0B8C3] hover:text-red-400 hover:bg-white/5 transition-colors"
                  title="Logout"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Hero / Welcome Section */}
        <div className="mb-10 text-center">
           <h2 className="text-3xl md:text-4xl font-bold text-white mb-2">
             Financial Clarity for <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00F0B5] to-[#2196F3]">Modern Business</span>
           </h2>
           <p className="text-[#B0B8C3] max-w-2xl mx-auto">
             Real-time cash flow analytics and budget tracking powered by AI.
           </p>
        </div>

        {isPersonalMode ? (
          // Personal Budget Dashboard
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Budget Health - Hero Card */}
            <div className="lg:col-span-2 bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-lg relative overflow-hidden group hover:border-[#00F0B5]/30 transition-all duration-300">
              <div className="absolute top-0 right-0 w-64 h-64 bg-[#00F0B5]/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
              
              <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center h-full">
                <div>
                  <h3 className="text-lg font-medium text-[#B0B8C3] mb-1">Total Balance</h3>
                  <div className="text-5xl font-bold text-white mb-4 tracking-tight">
                    RM {personalData.balance.toLocaleString()}
                  </div>
                  <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${
                    personalData.balance > 0 
                      ? 'bg-[#00F0B5]/10 border-[#00F0B5]/20 text-[#00F0B5]' 
                      : 'bg-red-500/10 border-red-500/20 text-red-400'
                  }`}>
                    <span className="w-2 h-2 rounded-full bg-current mr-2"></span>
                    {personalData.balance > 0 ? 'Healthy Budget' : 'Over Budget'}
                  </div>
                </div>
                
                <div className="mt-6 md:mt-0 grid grid-cols-2 gap-4 w-full md:w-auto">
                   <div className="bg-[#0A192F]/50 p-4 rounded-xl border border-white/5">
                      <p className="text-xs text-[#B0B8C3] mb-1">Income</p>
                      <p className="text-xl font-bold text-[#00F0B5]">+RM {personalData.totalIncome.toLocaleString()}</p>
                   </div>
                   <div className="bg-[#0A192F]/50 p-4 rounded-xl border border-white/5">
                      <p className="text-xs text-[#B0B8C3] mb-1">Spending</p>
                      <p className="text-xl font-bold text-white">-RM {personalData.totalSpending.toLocaleString()}</p>
                   </div>
                </div>
              </div>
            </div>

            {/* Quick Actions - Bento Style */}
            <div className="grid grid-rows-2 gap-6">
               <button 
                  onClick={() => setAddTransactionModalOpen(true)}
                  className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-lg hover:bg-[#00F0B5] hover:text-[#0A192F] group transition-all duration-300 flex flex-col justify-center items-center text-center"
                >
                  <div className="w-12 h-12 rounded-full bg-[#00F0B5]/10 text-[#00F0B5] group-hover:bg-[#0A192F]/10 group-hover:text-[#0A192F] flex items-center justify-center mb-3 transition-colors">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
                  </div>
                  <span className="font-semibold">Add Transaction</span>
               </button>
               
               <div className="grid grid-cols-2 gap-6">
                  <button onClick={() => setCurrentPage('reports')} className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-4 shadow-lg hover:border-[#00F0B5]/50 transition-all flex flex-col justify-center items-center">
                    <span className="text-2xl mb-2"><svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg></span>
                    <span className="text-sm text-[#B0B8C3]">Reports</span>
                  </button>
                  <button onClick={() => setSettingsModalOpen(true)} className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-4 shadow-lg hover:border-[#00F0B5]/50 transition-all flex flex-col justify-center items-center">
                    <span className="text-2xl mb-2"><svg className="w-6 h-6 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg></span>
                    <span className="text-sm text-[#B0B8C3]">Settings</span>
                  </button>
               </div>
            </div>
          </div>
        ) : (
          // Business Dashboard
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
             {/* CCC Hero Card */}
             <div className="lg:col-span-2 bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-lg relative overflow-hidden group hover:border-[#00F0B5]/30 transition-all duration-300">
                <div className="absolute top-0 right-0 w-64 h-64 bg-[#2196F3]/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
                
                <div className="relative z-10">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="text-2xl">{cccStatus.icon}</span>
                    <h3 className="text-lg font-medium text-[#B0B8C3]">Cash Conversion Cycle</h3>
                  </div>
                  
                  <div className="flex items-baseline space-x-4 mb-6">
                    <div className="text-5xl font-bold text-white tracking-tight">
                      {dashboardData.ccc} <span className="text-2xl text-[#B0B8C3] font-normal">days</span>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-sm font-medium border ${
                      cccStatus.status === 'Excellent' ? 'bg-[#00F0B5]/10 border-[#00F0B5]/20 text-[#00F0B5]' :
                      cccStatus.status === 'Good' ? 'bg-blue-500/10 border-blue-500/20 text-blue-400' :
                      'bg-orange-500/10 border-orange-500/20 text-orange-400'
                    }`}>
                      {cccStatus.status}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-[#0A192F]/50 p-4 rounded-xl border border-white/5">
                      <p className="text-xs text-[#B0B8C3] mb-1">DSO (Sales)</p>
                      <p className="text-xl font-bold text-white">{dashboardData.dso}</p>
                    </div>
                    <div className="bg-[#0A192F]/50 p-4 rounded-xl border border-white/5">
                      <p className="text-xs text-[#B0B8C3] mb-1">DIO (Inventory)</p>
                      <p className="text-xl font-bold text-white">{dashboardData.dio}</p>
                    </div>
                    <div className="bg-[#0A192F]/50 p-4 rounded-xl border border-white/5">
                      <p className="text-xs text-[#B0B8C3] mb-1">DPO (Payable)</p>
                      <p className="text-xl font-bold text-white">{dashboardData.dpo}</p>
                    </div>
                  </div>
                </div>
             </div>

             {/* Quick Actions - Business */}
             <div className="grid grid-rows-2 gap-6">
               <button 
                  onClick={() => setAddTransactionModalOpen(true)}
                  className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-lg hover:bg-[#00F0B5] hover:text-[#0A192F] group transition-all duration-300 flex flex-col justify-center items-center text-center"
                >
                  <div className="w-12 h-12 rounded-full bg-[#00F0B5]/10 text-[#00F0B5] group-hover:bg-[#0A192F]/10 group-hover:text-[#0A192F] flex items-center justify-center mb-3 transition-colors">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
                  </div>
                  <span className="font-semibold">New Entry</span>
               </button>
               
               <div className="grid grid-cols-2 gap-6">
                  <button onClick={() => setCurrentPage('reports')} className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-4 shadow-lg hover:border-[#00F0B5]/50 transition-all flex flex-col justify-center items-center">
                    <span className="text-2xl mb-2"><svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg></span>
                    <span className="text-sm text-[#B0B8C3]">Reports</span>
                  </button>
                  <button onClick={() => setSettingsModalOpen(true)} className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-4 shadow-lg hover:border-[#00F0B5]/50 transition-all flex flex-col justify-center items-center">
                    <span className="text-2xl mb-2"><svg className="w-6 h-6 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg></span>
                    <span className="text-sm text-[#B0B8C3]">Settings</span>
                  </button>
               </div>
            </div>
          </div>
        )}

        {/* Secondary Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Left Column: Charts/Summary */}
          <div className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-lg">
            <h3 className="text-lg font-bold text-white mb-6 flex items-center">
              <span className="w-1 h-6 bg-[#00F0B5] rounded-full mr-3"></span>
              {isPersonalMode ? 'Spending Categories' : 'Financial Summary (90 Days)'}
            </h3>
            
            {isPersonalMode ? (
              <div className="space-y-4">
                {personalData.categories.map((category) => (
                  <div key={category.name} className="group">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-[#B0B8C3] group-hover:text-white transition-colors">{category.name}</span>
                      <span className="text-white font-medium">RM {category.amount.toLocaleString()}</span>
                    </div>
                    <div className="w-full bg-[#0A192F] rounded-full h-1.5 overflow-hidden">
                      <div 
                        className="h-full rounded-full transition-all duration-500 ease-out" 
                        style={{
                          width: `${(category.amount / personalData.totalSpending) * 100}%`, 
                          backgroundColor: category.color
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#0A192F]/30 p-4 rounded-xl border border-white/5 hover:border-[#00F0B5]/20 transition-colors">
                  <p className="text-xs text-[#B0B8C3] mb-1">Total Sales</p>
                  <p className="text-lg font-bold text-[#00F0B5]">RM {dashboardData.summary.totalSales.toLocaleString()}</p>
                </div>
                <div className="bg-[#0A192F]/30 p-4 rounded-xl border border-white/5 hover:border-[#2196F3]/20 transition-colors">
                  <p className="text-xs text-[#B0B8C3] mb-1">Purchases</p>
                  <p className="text-lg font-bold text-[#2196F3]">RM {dashboardData.summary.totalPurchases.toLocaleString()}</p>
                </div>
                <div className="bg-[#0A192F]/30 p-4 rounded-xl border border-white/5 hover:border-[#00F0B5]/20 transition-colors">
                  <p className="text-xs text-[#B0B8C3] mb-1">Received</p>
                  <p className="text-lg font-bold text-[#00F0B5]">RM {dashboardData.summary.totalPaymentsReceived.toLocaleString()}</p>
                </div>
                <div className="bg-[#0A192F]/30 p-4 rounded-xl border border-white/5 hover:border-orange-400/20 transition-colors">
                  <p className="text-xs text-[#B0B8C3] mb-1">Paid</p>
                  <p className="text-lg font-bold text-orange-400">RM {dashboardData.summary.totalPaymentsMade.toLocaleString()}</p>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Recent Transactions */}
          <div className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-lg">
            <h3 className="text-lg font-bold text-white mb-6 flex items-center">
              <span className="w-1 h-6 bg-[#2196F3] rounded-full mr-3"></span>
              Recent Activity
            </h3>
            
            <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
              {(isPersonalMode ? personalData.recentTransactions : dashboardData.recentTransactions).length > 0 ? (
                (isPersonalMode ? personalData.recentTransactions : dashboardData.recentTransactions).map((transaction, idx) => (
                  <div key={transaction.id || idx} className="flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-colors border border-transparent hover:border-white/5">
                    <div className="flex items-center space-x-3">
                      <div className={`w-2 h-2 rounded-full ${
                        (transaction.type || '') === 'sale' || (transaction.type || '') === 'payment_received' ? 'bg-[#00F0B5] shadow-[0_0_8px_#00F0B5]' :
                        'bg-[#2196F3] shadow-[0_0_8px_#2196F3]'
                      }`}></div>
                      <div>
                        <p className="text-sm font-medium text-white">{transaction.customer || transaction.description || 'Transaction'}</p>
                        <p className="text-xs text-[#B0B8C3]">{transaction.date}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-bold ${
                        (transaction.type || '') === 'sale' || (transaction.type || '') === 'payment_received' 
                          ? 'text-[#00F0B5]' : 'text-white'
                      }`}>
                        {(transaction.type || '') === 'sale' || (transaction.type || '') === 'payment_received' ? '+' : '-'}RM {transaction.amount}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-[#B0B8C3]">
                  <p>No recent transactions found.</p>
                </div>
              )}
            </div>
          </div>

        </div>
      </main>

      {/* Modals */}
      <AddTransactionModal
        isOpen={addTransactionModalOpen}
        onClose={() => setAddTransactionModalOpen(false)}
        onSubmit={handleAddTransaction}
        user={user}
      />

      <SettingsModal
        isOpen={settingsModalOpen}
        onClose={() => setSettingsModalOpen(false)}
        user={user}
        onUserUpdate={handleUserUpdate}
        authToken={authToken}
      />

      <HelpModal
        isOpen={helpModalOpen}
        onClose={() => setHelpModalOpen(false)}
      />
    </div>
  )
}

export default App
