import { useState, useEffect } from 'react'
import { buildApiUrl } from '../config/api'

function PersonalDashboard({ user, authToken }) {
  const [dashboardData, setDashboardData] = useState({
    period: { start: '', end: '' },
    summary: {
      total_income: 0,
      total_expenses: 0,
      net_income: 0,
      transaction_count: 0
    },
    category_breakdown: {},
    recent_transactions: []
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (user?.wa_id) {
      fetchDashboardData()
    }
  }, [user])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const response = await fetch(buildApiUrl(`/api/personal/dashboard/${user.wa_id}`), {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        if (response.status === 403) {
          const errorData = await response.json().catch(() => ({ error: 'Personal budget feature not enabled' }))
          throw new Error(errorData.error || 'Personal budget feature not available')
        }
        throw new Error(`Error: ${response.status}`)
      }

      const data = await response.json()
      setDashboardData(data)
    } catch (err) {
      console.error('Error fetching personal dashboard:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-MY', {
      style: 'currency',
      currency: 'MYR'
    }).format(amount)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-MY', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6" style={{
        background: 'linear-gradient(135deg, #F5F5F5 0%, #F8F9FA 20%, #F5F5F5 40%, rgba(76, 175, 80, 0.02) 60%, #F5F5F5 80%, rgba(255, 179, 0, 0.01) 100%)',
        backgroundSize: '400% 400%',
        animation: 'subtleShift 20s ease-in-out infinite'
      }}>
        <div className="neuro-card p-8 text-center">
          <div className="neuro-icon w-16 h-16 mx-auto mb-4 flex items-center justify-center animate-pulse">
            <span className="text-2xl">💰</span>
          </div>
          <h3 className="text-xl font-bold text-gray-800 mb-2">Loading Dashboard</h3>
          <p className="text-gray-600">Fetching your personal financial data...</p>
          <div className="mt-4 flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-gray-700"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    const isFeatureDisabled = error.includes('not enabled') || error.includes('not available')
    
    return (
      <div className="min-h-screen flex items-center justify-center p-6" style={{
        background: 'linear-gradient(135deg, #F5F5F5 0%, #F8F9FA 20%, #F5F5F5 40%, rgba(76, 175, 80, 0.02) 60%, #F5F5F5 80%, rgba(255, 179, 0, 0.01) 100%)',
        backgroundSize: '400% 400%',
        animation: 'subtleShift 20s ease-in-out infinite'
      }}>
        <div className="neuro-card p-8 text-center max-w-md">
          <div className="neuro-icon w-16 h-16 mx-auto mb-4 flex items-center justify-center">
            <span className="text-2xl">{isFeatureDisabled ? '🔧' : '⚠️'}</span>
          </div>
          <h3 className="text-2xl font-bold text-gray-800 mb-4">
            {isFeatureDisabled ? 'Feature Not Available' : 'Error'}
          </h3>
          <p className="text-lg text-gray-600 mb-4">{error}</p>
          {isFeatureDisabled && (
            <div className="neuro-card p-4 text-left">
              <p className="text-sm text-gray-700">
                The personal budget feature is currently disabled on this server. 
                Please contact support or check your server configuration.
              </p>
            </div>
          )}
          <button 
            onClick={() => window.location.reload()} 
            className="neuro-button mt-6 px-6 py-3 font-semibold text-gray-800"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-6" style={{
      background: 'linear-gradient(135deg, #F5F5F5 0%, #F8F9FA 20%, #F5F5F5 40%, rgba(76, 175, 80, 0.02) 60%, #F5F5F5 80%, rgba(255, 179, 0, 0.01) 100%)',
      backgroundSize: '400% 400%',
      animation: 'subtleShift 20s ease-in-out infinite'
    }}>
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-800 mb-4 drop-shadow-sm">Personal Budget Dashboard</h1>
          <p className="text-lg text-gray-600">
            {dashboardData.period.start && dashboardData.period.end && (
              `Period: ${formatDate(dashboardData.period.start)} - ${formatDate(dashboardData.period.end)}`
            )}
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div className="neuro-card p-6 text-center">
            <div className="neuro-icon w-16 h-16 mx-auto mb-4 flex items-center justify-center">
              <span className="text-2xl">💰</span>
            </div>
            <h3 className="text-sm font-medium text-gray-600 mb-2">Total Income</h3>
            <p className="text-2xl font-bold text-gray-800">
              {formatCurrency(dashboardData.summary.total_income)}
            </p>
          </div>
          
          <div className="neuro-card p-6 text-center">
            <div className="neuro-icon w-16 h-16 mx-auto mb-4 flex items-center justify-center">
              <span className="text-2xl">💸</span>
            </div>
            <h3 className="text-sm font-medium text-gray-600 mb-2">Total Expenses</h3>
            <p className="text-2xl font-bold text-gray-800">
              {formatCurrency(dashboardData.summary.total_expenses)}
            </p>
          </div>
          
          <div className="neuro-card p-6 text-center">
            <div className="neuro-icon w-16 h-16 mx-auto mb-4 flex items-center justify-center">
              <span className="text-2xl">{dashboardData.summary.net_income >= 0 ? '📈' : '📉'}</span>
            </div>
            <h3 className="text-sm font-medium text-gray-600 mb-2">Net Income</h3>
            <p className={`text-2xl font-bold ${dashboardData.summary.net_income >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(dashboardData.summary.net_income)}
            </p>
          </div>
          
          <div className="neuro-card p-6 text-center">
            <div className="neuro-icon w-16 h-16 mx-auto mb-4 flex items-center justify-center">
              <span className="text-2xl">📊</span>
            </div>
            <h3 className="text-sm font-medium text-gray-600 mb-2">Transactions</h3>
            <p className="text-2xl font-bold text-gray-800">
              {dashboardData.summary.transaction_count}
            </p>
          </div>
        </div>

        {/* Category Breakdown */}
        {Object.keys(dashboardData.category_breakdown).length > 0 && (
          <div className="neuro-card p-8">
            <h3 className="text-2xl font-bold text-gray-800 mb-6 text-center">Spending by Category</h3>
            <div className="space-y-4">
              {Object.entries(dashboardData.category_breakdown)
                .sort(([,a], [,b]) => b - a)
                .map(([category, amount]) => (
                  <div key={category} className="neuro-card p-4 flex justify-between items-center">
                    <span className="text-lg font-medium text-gray-700 capitalize">
                      {category.replace(/_/g, ' ')}
                    </span>
                    <span className="text-lg text-gray-800 font-bold">
                      {formatCurrency(amount)}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Recent Transactions */}
        {dashboardData.recent_transactions.length > 0 && (
          <div className="neuro-card p-8">
            <h3 className="text-2xl font-bold text-gray-800 mb-6 text-center">Recent Transactions</h3>
            <div className="space-y-4">
              {dashboardData.recent_transactions.map((transaction, index) => (
                <div key={transaction.id || index} className="neuro-card p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="text-lg font-medium text-gray-800">
                        {transaction.description || 'No description'}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        <span className="capitalize">{transaction.category?.replace(/_/g, ' ')}</span> • {formatDate(transaction.timestamp)}
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      <span className={`text-lg font-bold ${
                        transaction.action === 'income' 
                          ? 'text-green-600' 
                          : 'text-red-600'
                      }`}>
                        {transaction.action === 'income' ? '+' : '-'}{formatCurrency(transaction.amount)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {dashboardData.summary.transaction_count === 0 && (
          <div className="neuro-card p-8 text-center">
            <div className="neuro-icon w-24 h-24 mx-auto mb-6 flex items-center justify-center">
              <span className="text-4xl">📱</span>
            </div>
            <h3 className="text-2xl font-bold text-gray-800 mb-4">No transactions yet</h3>
            <p className="text-lg text-gray-600 mb-8">
              Start by sending a WhatsApp message like "beli nasi lemak rm 5" to track your expenses!
            </p>
            <div className="neuro-card p-6 text-left">
              <h4 className="text-xl font-bold text-gray-800 mb-4 text-center">Example messages:</h4>
              <ul className="text-lg text-gray-700 space-y-3">
                <li className="flex items-center">
                  <span className="neuro-icon w-8 h-8 mr-3 flex items-center justify-center text-sm">🍛</span>
                  "beli nasi lemak rm 5" (Food expense)
                </li>
                <li className="flex items-center">
                  <span className="neuro-icon w-8 h-8 mr-3 flex items-center justify-center text-sm">💰</span>
                  "gaji masuk rm 3000" (Income)
                </li>
                <li className="flex items-center">
                  <span className="neuro-icon w-8 h-8 mr-3 flex items-center justify-center text-sm">⚡</span>
                  "bayar bil elektrik rm 80" (Utilities)
                </li>
                <li className="flex items-center">
                  <span className="neuro-icon w-8 h-8 mr-3 flex items-center justify-center text-sm">🚗</span>
                  "grab ke office rm 12" (Transportation)
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PersonalDashboard