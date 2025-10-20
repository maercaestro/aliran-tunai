import { useState, useEffect } from 'react'
import AddTransactionModal from '../AddTransactionModal'
import SettingsModal from '../SettingsModal'
import HelpModal from '../HelpModal'
import { buildApiUrl, API_ENDPOINTS } from '../../config/api'

function BusinessDashboard({ user, authToken, onLogout, onModeChange }) {
  // State for dashboard data (copied from original App.jsx)
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
  const [lastUpdated, setLastUpdated] = useState(null)

  // Modal states
  const [addTransactionModalOpen, setAddTransactionModalOpen] = useState(false)
  const [settingsModalOpen, setSettingsModalOpen] = useState(false)
  const [helpModalOpen, setHelpModalOpen] = useState(false)

  useEffect(() => {
    if (user && authToken) {
      fetchDashboardData()
    }
  }, [user, authToken])

  // Fetch dashboard data from API (copied from original App.jsx)
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
          onLogout()
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading business dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Business Dashboard</h1>
              <p className="text-gray-600">Cash Flow Management</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => onModeChange('personal')}
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-lg hover:bg-gray-100"
              >
                Switch to Personal
              </button>
              <button
                onClick={onLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
                <div className="mt-4">
                  <button
                    onClick={fetchDashboardData}
                    className="bg-red-100 text-red-800 px-3 py-1 rounded-md text-sm font-medium hover:bg-red-200"
                  >
                    Try Again
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* CCC Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-blue-100 text-blue-600">
                🔄
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Cash Conversion Cycle</p>
                <p className="text-2xl font-bold text-gray-900">{dashboardData.ccc} days</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100 text-green-600">
                📈
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Days Sales Outstanding</p>
                <p className="text-2xl font-bold text-gray-900">{dashboardData.dso} days</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
                📦
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Days Inventory Outstanding</p>
                <p className="text-2xl font-bold text-gray-900">{dashboardData.dio} days</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-purple-100 text-purple-600">
                💳
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Days Payable Outstanding</p>
                <p className="text-2xl font-bold text-gray-900">{dashboardData.dpo} days</p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-4 mb-8">
          <button
            onClick={() => setAddTransactionModalOpen(true)}
            className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 font-medium"
          >
            Add Transaction
          </button>
          <button
            onClick={fetchDashboardData}
            className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 font-medium"
          >
            Refresh Data
          </button>
          <button
            onClick={() => setSettingsModalOpen(true)}
            className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 font-medium"
          >
            Settings
          </button>
        </div>

        {/* Transaction Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Total Sales</h3>
            <p className="text-3xl font-bold text-green-600">${dashboardData.summary.totalSales.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Total Purchases</h3>
            <p className="text-3xl font-bold text-red-600">${dashboardData.summary.totalPurchases.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Payments Received</h3>
            <p className="text-3xl font-bold text-blue-600">${dashboardData.summary.totalPaymentsReceived.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Payments Made</h3>
            <p className="text-3xl font-bold text-purple-600">${dashboardData.summary.totalPaymentsMade.toLocaleString()}</p>
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Transactions</h3>
          </div>
          <div className="p-6">
            {dashboardData.recentTransactions.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {dashboardData.recentTransactions.slice(0, 10).map((transaction, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(transaction.timestamp).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                            transaction.action === 'sale' ? 'bg-green-100 text-green-800' :
                            transaction.action === 'purchase' ? 'bg-red-100 text-red-800' :
                            transaction.action === 'payment_received' ? 'bg-blue-100 text-blue-800' :
                            'bg-purple-100 text-purple-800'
                          }`}>
                            {transaction.action}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          ${transaction.amount.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {transaction.description}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No recent transactions</p>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      <AddTransactionModal
        isOpen={addTransactionModalOpen}
        onClose={() => setAddTransactionModalOpen(false)}
        onTransactionAdded={fetchDashboardData}
        user={user}
        authToken={authToken}
      />

      <SettingsModal
        isOpen={settingsModalOpen}
        onClose={() => setSettingsModalOpen(false)}
        user={user}
        authToken={authToken}
      />

      <HelpModal
        isOpen={helpModalOpen}
        onClose={() => setHelpModalOpen(false)}
      />
    </div>
  )
}

export default BusinessDashboard