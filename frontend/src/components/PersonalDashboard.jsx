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
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2">Loading your personal dashboard...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        <strong className="font-bold">Error:</strong>
        <span className="block sm:inline"> {error}</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Personal Budget Dashboard</h1>
        <p className="text-gray-600">
          {dashboardData.period.start && dashboardData.period.end && (
            `Period: ${formatDate(dashboardData.period.start)} - ${formatDate(dashboardData.period.end)}`
          )}
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-green-800">Total Income</h3>
          <p className="text-2xl font-bold text-green-900">
            {formatCurrency(dashboardData.summary.total_income)}
          </p>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-red-800">Total Expenses</h3>
          <p className="text-2xl font-bold text-red-900">
            {formatCurrency(dashboardData.summary.total_expenses)}
          </p>
        </div>
        
        <div className={`${dashboardData.summary.net_income >= 0 ? 'bg-blue-50 border-blue-200' : 'bg-orange-50 border-orange-200'} rounded-lg p-4`}>
          <h3 className={`text-sm font-medium ${dashboardData.summary.net_income >= 0 ? 'text-blue-800' : 'text-orange-800'}`}>
            Net Income
          </h3>
          <p className={`text-2xl font-bold ${dashboardData.summary.net_income >= 0 ? 'text-blue-900' : 'text-orange-900'}`}>
            {formatCurrency(dashboardData.summary.net_income)}
          </p>
        </div>
        
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-800">Transactions</h3>
          <p className="text-2xl font-bold text-gray-900">
            {dashboardData.summary.transaction_count}
          </p>
        </div>
      </div>

      {/* Category Breakdown */}
      {Object.keys(dashboardData.category_breakdown).length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Spending by Category</h3>
          <div className="space-y-3">
            {Object.entries(dashboardData.category_breakdown)
              .sort(([,a], [,b]) => b - a)
              .map(([category, amount]) => (
                <div key={category} className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">
                    {category.replace(/_/g, ' ')}
                  </span>
                  <span className="text-sm text-gray-900 font-semibold">
                    {formatCurrency(amount)}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Recent Transactions */}
      {dashboardData.recent_transactions.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Transactions</h3>
          <div className="space-y-3">
            {dashboardData.recent_transactions.map((transaction, index) => (
              <div key={transaction.id || index} className="flex justify-between items-start py-2 border-b border-gray-100 last:border-b-0">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    {transaction.description || 'No description'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {transaction.category?.replace(/_/g, ' ')} • {formatDate(transaction.timestamp)}
                  </p>
                </div>
                <span className={`text-sm font-semibold ${
                  transaction.action === 'income' 
                    ? 'text-green-600' 
                    : 'text-red-600'
                }`}>
                  {transaction.action === 'income' ? '+' : '-'}{formatCurrency(transaction.amount)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {dashboardData.summary.transaction_count === 0 && (
        <div className="text-center py-8">
          <h3 className="text-lg font-medium text-gray-900 mb-2">No transactions yet</h3>
          <p className="text-gray-500 mb-4">
            Start by sending a WhatsApp message like "beli nasi lemak rm 5" to track your expenses!
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left">
            <h4 className="font-medium text-blue-900 mb-2">Example messages:</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• "beli nasi lemak rm 5" (Food expense)</li>
              <li>• "gaji masuk rm 3000" (Income)</li>
              <li>• "bayar bil elektrik rm 80" (Utilities)</li>
              <li>• "grab ke office rm 12" (Transportation)</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

export default PersonalDashboard