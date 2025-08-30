import { useState, useEffect } from 'react'

function App() {
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
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [chatId, setChatId] = useState(123456) // Default chat_id from database
  const [lastUpdated, setLastUpdated] = useState(null)

  // Fetch dashboard data from API
  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`http://localhost:5001/api/dashboard/${chatId}`)
      
      if (!response.ok) {
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
  useEffect(() => {
    fetchDashboardData()
  }, [chatId])

  const getCCCStatus = (ccc) => {
    if (ccc < 30) return { color: 'text-emerald-600', bg: 'from-emerald-50 to-emerald-100', status: 'Excellent', icon: '🎉' }
    if (ccc < 60) return { color: 'text-blue-600', bg: 'from-blue-50 to-blue-100', status: 'Good', icon: '👍' }
    if (ccc < 90) return { color: 'text-orange-600', bg: 'from-orange-50 to-orange-100', status: 'Moderate', icon: '⚠️' }
    return { color: 'text-red-600', bg: 'from-red-50 to-red-100', status: 'Needs Attention', icon: '🚨' }
  }

  const cccStatus = getCCCStatus(dashboardData.ccc)

  // Loading state
  if (loading) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center" style={{background: '#F5F5F5'}}>
        <div className="neuro-card p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#2196F3] mx-auto mb-4"></div>
          <p className="text-[#424242] text-lg">Loading your financial dashboard...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center" style={{background: '#F5F5F5'}}>
        <div className="neuro-card p-8 text-center max-w-md">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-[#424242] mb-2">Connection Error</h2>
          <p className="text-[#BDBDBD] mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="neuro-button px-6 py-3 text-[#424242] font-medium"
          >
            Try Again
          </button>
          <div className="mt-4 p-3 bg-[#FFB300]/10 rounded-lg">
            <p className="text-sm text-[#424242]">
              <strong>Note:</strong> Make sure the API server is running on port 5001
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full min-h-screen relative" style={{background: '#F5F5F5'}}>
      
      {/* Background Logo Watermark */}
      <div className="fixed inset-0 flex items-center justify-center pointer-events-none z-0">
        <img 
          src="/logoaliran.png" 
          alt="Background Logo" 
          className="w-120 h-120 opacity-20"
          style={{
            filter: 'blur(2px)',
            transform: 'rotate(-15deg)'
          }}
        />
      </div>
      
      {/* Header */}
      <header className="relative z-10" style={{
        background: '#F5F5F5',
        boxShadow: '0 4px 8px rgba(0, 0, 0, 0.05), 0 -4px 8px rgba(255, 255, 255, 0.6)',
        borderBottom: '1px solid rgba(189, 189, 189, 0.2)'
      }}>
        <div className="w-full max-w-none px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <img src="/logoaliran.png" alt="AliranTunai Logo" className="h-20 w-20 rounded-lg" />
              <div>
                <h1 className="text-2xl font-bold text-[#424242]">AliranTunai</h1>
                <span className="text-sm text-[#BDBDBD]">Cash Flow Dashboard</span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <label className="text-sm text-[#BDBDBD]">User ID:</label>
                <input 
                  type="number" 
                  value={chatId} 
                  onChange={(e) => setChatId(Number(e.target.value) || 123456)}
                  placeholder="123456"
                  className="neuro-card-inset px-3 py-1 text-sm text-[#424242] w-32 border-none outline-none"
                  style={{background: '#F5F5F5'}}
                />
              </div>
              <button 
                onClick={fetchDashboardData}
                disabled={loading}
                className="neuro-button px-3 py-1 text-sm text-[#424242] disabled:opacity-50"
              >
                {loading ? '↻' : '🔄'}
              </button>
              <div className="text-right">
                <div className="text-sm text-[#BDBDBD]">
                  {dashboardData.totalTransactions > 0 ? 
                    `${dashboardData.totalTransactions} transactions` : 
                    'No data'
                  }
                </div>
                {lastUpdated && (
                  <div className="text-xs text-[#BDBDBD]">
                    Updated: {lastUpdated.toLocaleTimeString()}
                  </div>
                )}
              </div>
              <div className="neuro-button w-10 h-10 flex items-center justify-center">
                <span className="text-[#424242] text-sm font-medium">U</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 w-full px-4 sm:px-6 lg:px-8 py-8">
        {/* CCC Overview Card */}
        <div className="neuro-card p-8 mb-8 border-l-4" style={{borderLeftColor: '#4CAF50'}}>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-2xl">{cccStatus.icon}</span>
                <h2 className="!text-2xl font-bold !text-[#424242]">Cash Conversion Cycle</h2>
              </div>
              <p className="!text-[#BDBDBD] mt-1">How long your money is tied up in operations</p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold bg-gradient-to-r from-[#2196F3] to-[#4CAF50] bg-clip-text text-transparent mb-1">
                {dashboardData.ccc} days
              </div>
              <div className={`text-sm font-semibold px-3 py-1 rounded-full ${cccStatus.color}`} 
                   style={{
                     background: '!#F5F5F5',
                     boxShadow: 'inset 4px 4px 8px rgba(0, 0, 0, 0.05), inset -4px -4px 8px rgba(255, 255, 255, 0.6)'
                   }}>
                {cccStatus.status}
              </div>
            </div>
          </div>
        </div>

        {/* CCC Components */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="neuro-card p-6">
            <div className="flex items-center">
              <div className="neuro-button p-3" style={{
                background: 'linear-gradient(135deg, #2196F3, #4CAF50)',
                color: 'white'
              }}>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-[#BDBDBD]">Days Sales Outstanding</p>
                <p className="text-2xl font-bold text-[#424242]">{dashboardData.dso} days</p>
                <p className="text-xs text-[#BDBDBD]">Time to collect payments</p>
              </div>
            </div>
          </div>

          <div className="neuro-card p-6">
            <div className="flex items-center">
              <div className="neuro-button p-3" style={{
                background: 'linear-gradient(135deg, #FFB300, #4CAF50)',
                color: 'white'
              }}>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-[#BDBDBD]">Days Inventory Outstanding</p>
                <p className="text-2xl font-bold text-[#424242]">{dashboardData.dio} days</p>
                <p className="text-xs text-[#BDBDBD]">Inventory turnover time</p>
              </div>
            </div>
          </div>

          <div className="neuro-card p-6">
            <div className="flex items-center">
              <div className="neuro-button p-3" style={{
                background: 'linear-gradient(135deg, #2196F3, #FFB300)',
                color: 'white'
              }}>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v2a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-[#BDBDBD]">Days Payable Outstanding</p>
                <p className="text-2xl font-bold text-[#424242]">{dashboardData.dpo} days</p>
                <p className="text-xs text-[#BDBDBD]">Time to pay suppliers</p>
              </div>
            </div>
          </div>
        </div>

        {/* Financial Summary */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Summary Cards */}
          <div className="neuro-card">
            <div className="p-6" style={{borderBottom: '1px solid rgba(189, 189, 189, 0.2)'}}>
              <h3 className="text-xl font-bold text-[#424242]">Financial Summary (90 days)</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="neuro-card-inset text-center p-4">
                  <p className="text-sm text-[#BDBDBD] mb-1">Total Sales</p>
                  <p className="text-xl font-bold text-[#4CAF50]">RM {dashboardData.summary.totalSales.toLocaleString()}</p>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2" style={{
                    boxShadow: 'inset 2px 2px 4px rgba(0, 0, 0, 0.1), inset -2px -2px 4px rgba(255, 255, 255, 0.6)'
                  }}>
                    <div className="h-2 rounded-full" style={{width: '75%', background: '#4CAF50'}}></div>
                  </div>
                </div>
                <div className="neuro-card-inset text-center p-4">
                  <p className="text-sm text-[#BDBDBD] mb-1">Total Purchases</p>
                  <p className="text-xl font-bold text-[#2196F3]">RM {dashboardData.summary.totalPurchases.toLocaleString()}</p>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2" style={{
                    boxShadow: 'inset 2px 2px 4px rgba(0, 0, 0, 0.1), inset -2px -2px 4px rgba(255, 255, 255, 0.6)'
                  }}>
                    <div className="h-2 rounded-full" style={{width: '60%', background: '#2196F3'}}></div>
                  </div>
                </div>
                <div className="neuro-card-inset text-center p-4">
                  <p className="text-sm text-[#BDBDBD] mb-1">Payments Received</p>
                  <p className="text-xl font-bold text-[#4CAF50]">RM {dashboardData.summary.totalPaymentsReceived.toLocaleString()}</p>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2" style={{
                    boxShadow: 'inset 2px 2px 4px rgba(0, 0, 0, 0.1), inset -2px -2px 4px rgba(255, 255, 255, 0.6)'
                  }}>
                    <div className="h-2 rounded-full" style={{width: '40%', background: '#4CAF50'}}></div>
                  </div>
                </div>
                <div className="neuro-card-inset text-center p-4">
                  <p className="text-sm text-[#BDBDBD] mb-1">Payments Made</p>
                  <p className="text-xl font-bold text-[#FFB300]">RM {dashboardData.summary.totalPaymentsMade.toLocaleString()}</p>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2" style={{
                    boxShadow: 'inset 2px 2px 4px rgba(0, 0, 0, 0.1), inset -2px -2px 4px rgba(255, 255, 255, 0.6)'
                  }}>
                    <div className="h-2 rounded-full" style={{width: '80%', background: '#FFB300'}}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Transactions */}
          <div className="neuro-card">
            <div className="p-6" style={{borderBottom: '1px solid rgba(189, 189, 189, 0.2)'}}>
              <h3 className="text-xl font-bold text-[#424242]">Recent Transactions</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {dashboardData.recentTransactions.map((transaction) => (
                  <div key={transaction.id} className="neuro-card-inset flex items-center justify-between p-4">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${
                        transaction.type === 'sale' ? 'bg-[#4CAF50]' :
                        transaction.type === 'purchase' ? 'bg-[#2196F3]' :
                        transaction.type === 'payment_received' ? 'bg-[#4CAF50]' : 'bg-[#FFB300]'
                      }`} style={{
                        boxShadow: '2px 2px 4px rgba(0, 0, 0, 0.1), -2px -2px 4px rgba(255, 255, 255, 0.6)'
                      }}></div>
                      <div>
                        <p className="text-sm font-medium text-[#424242]">{transaction.customer}</p>
                        <p className="text-xs text-[#BDBDBD]">{transaction.date} • {transaction.type.replace('_', ' ')}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-bold ${
                        transaction.type === 'sale' || transaction.type === 'payment_received' 
                          ? 'text-[#4CAF50]' : 'text-[#2196F3]'
                      }`}>
                        {transaction.type === 'sale' || transaction.type === 'payment_received' ? '+' : '-'}RM {transaction.amount}
                      </p>
                      <div className={`text-xs px-2 py-1 rounded-full ${
                        transaction.status === 'completed' ? 'text-[#4CAF50]' : 'text-[#FFB300]'
                      }`} style={{
                        background: '#F5F5F5',
                        boxShadow: 'inset 2px 2px 4px rgba(0, 0, 0, 0.05), inset -2px -2px 4px rgba(255, 255, 255, 0.6)'
                      }}>
                        {transaction.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 neuro-card p-6">
          <h3 className="text-xl font-bold text-[#424242] mb-6">Quick Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button className="neuro-button p-6 group">
              <div className="text-center">
                <div className="w-12 h-12 mx-auto mb-3 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform" style={{
                  background: 'linear-gradient(135deg, #2196F3, #4CAF50)',
                  color: 'white',
                  boxShadow: '4px 4px 8px rgba(0, 0, 0, 0.1), -4px -4px 8px rgba(255, 255, 255, 0.6)'
                }}>
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-[#424242]">Add Transaction</p>
              </div>
            </button>
            <button className="neuro-button p-6 group">
              <div className="text-center">
                <div className="w-12 h-12 mx-auto mb-3 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform" style={{
                  background: 'linear-gradient(135deg, #FFB300, #4CAF50)',
                  color: 'white',
                  boxShadow: '4px 4px 8px rgba(0, 0, 0, 0.1), -4px -4px 8px rgba(255, 255, 255, 0.6)'
                }}>
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-[#424242]">View Reports</p>
              </div>
            </button>
            <button className="neuro-button p-6 group">
              <div className="text-center">
                <div className="w-12 h-12 mx-auto mb-3 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform" style={{
                  background: 'linear-gradient(135deg, #2196F3, #FFB300)',
                  color: 'white',
                  boxShadow: '4px 4px 8px rgba(0, 0, 0, 0.1), -4px -4px 8px rgba(255, 255, 255, 0.6)'
                }}>
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-[#424242]">Settings</p>
              </div>
            </button>
            <button className="neuro-button p-6 group">
              <div className="text-center">
                <div className="w-12 h-12 mx-auto mb-3 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform" style={{
                  background: 'linear-gradient(135deg, #4CAF50, #FFB300)',
                  color: 'white',
                  boxShadow: '4px 4px 8px rgba(0, 0, 0, 0.1), -4px -4px 8px rgba(255, 255, 255, 0.6)'
                }}>
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-[#424242]">Help</p>
              </div>
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
