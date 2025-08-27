import { useState } from 'react'

function App() {
  // Mock data based on your actual CCC calculations
  const [dashboardData] = useState({
    ccc: 74.7,
    dso: 13.4,
    dio: 61.3,
    dpo: 0.0,
    totalTransactions: 27,
    recentTransactions: [
      { id: 1, date: '2025-08-27', type: 'sale', amount: 300, customer: 'Kedai Ahmad', status: 'completed' },
      { id: 2, date: '2025-08-27', type: 'payment_received', amount: 50, customer: 'Walk-in Customer', status: 'completed' },
      { id: 3, date: '2025-08-26', type: 'purchase', amount: 1000, customer: 'SupplyCo', status: 'pending' },
      { id: 4, date: '2025-08-26', type: 'payment_made', amount: 1000, customer: 'SupplyCo', status: 'completed' },
    ],
    summary: {
      totalSales: 1245,
      totalPurchases: 1465,
      totalPaymentsReceived: 800,
      totalPaymentsMade: 2000
    }
  })

  const getCCCStatus = (ccc) => {
    if (ccc < 30) return { color: 'text-green-600', bg: 'bg-green-50', status: 'Excellent' }
    if (ccc < 60) return { color: 'text-yellow-600', bg: 'bg-yellow-50', status: 'Good' }
    if (ccc < 90) return { color: 'text-orange-600', bg: 'bg-orange-50', status: 'Moderate' }
    return { color: 'text-red-600', bg: 'bg-red-50', status: 'Needs Attention' }
  }

  const cccStatus = getCCCStatus(dashboardData.ccc)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">AliranTunai</h1>
              <span className="ml-2 text-sm text-gray-500">Cash Flow Dashboard</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">Last updated: Today</span>
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">U</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* CCC Overview Card */}
        <div className={`${cccStatus.bg} rounded-lg p-6 mb-8 border-l-4 border-blue-500`}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Cash Conversion Cycle</h2>
              <p className="text-sm text-gray-600 mt-1">How long your money is tied up in operations</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-gray-900">{dashboardData.ccc} days</div>
              <div className={`text-sm font-medium ${cccStatus.color}`}>{cccStatus.status}</div>
            </div>
          </div>
        </div>

        {/* CCC Components */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-md">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Days Sales Outstanding</p>
                <p className="text-2xl font-semibold text-gray-900">{dashboardData.dso} days</p>
                <p className="text-xs text-gray-500">Time to collect payments</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-md">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Days Inventory Outstanding</p>
                <p className="text-2xl font-semibold text-gray-900">{dashboardData.dio} days</p>
                <p className="text-xs text-gray-500">Inventory turnover time</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-md">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v2a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Days Payable Outstanding</p>
                <p className="text-2xl font-semibold text-gray-900">{dashboardData.dpo} days</p>
                <p className="text-xs text-gray-500">Time to pay suppliers</p>
              </div>
            </div>
          </div>
        </div>

        {/* Financial Summary */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Summary Cards */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Financial Summary (90 days)</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-sm text-gray-600">Total Sales</p>
                  <p className="text-xl font-semibold text-green-600">RM {dashboardData.summary.totalSales.toLocaleString()}</p>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <p className="text-sm text-gray-600">Total Purchases</p>
                  <p className="text-xl font-semibold text-red-600">RM {dashboardData.summary.totalPurchases.toLocaleString()}</p>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-gray-600">Payments Received</p>
                  <p className="text-xl font-semibold text-blue-600">RM {dashboardData.summary.totalPaymentsReceived.toLocaleString()}</p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <p className="text-sm text-gray-600">Payments Made</p>
                  <p className="text-xl font-semibold text-purple-600">RM {dashboardData.summary.totalPaymentsMade.toLocaleString()}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Transactions */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent Transactions</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {dashboardData.recentTransactions.map((transaction) => (
                  <div key={transaction.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-2 h-2 rounded-full ${
                        transaction.type === 'sale' ? 'bg-green-500' :
                        transaction.type === 'purchase' ? 'bg-red-500' :
                        transaction.type === 'payment_received' ? 'bg-blue-500' : 'bg-purple-500'
                      }`}></div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{transaction.customer}</p>
                        <p className="text-xs text-gray-500">{transaction.date} • {transaction.type.replace('_', ' ')}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-medium ${
                        transaction.type === 'sale' || transaction.type === 'payment_received' 
                          ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {transaction.type === 'sale' || transaction.type === 'payment_received' ? '+' : '-'}RM {transaction.amount}
                      </p>
                      <p className={`text-xs ${
                        transaction.status === 'completed' ? 'text-green-500' : 'text-yellow-500'
                      }`}>
                        {transaction.status}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors">
              <div className="text-center">
                <svg className="w-8 h-8 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <p className="text-sm text-gray-600">Add Transaction</p>
              </div>
            </button>
            <button className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors">
              <div className="text-center">
                <svg className="w-8 h-8 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="text-sm text-gray-600">View Reports</p>
              </div>
            </button>
            <button className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors">
              <div className="text-center">
                <svg className="w-8 h-8 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <p className="text-sm text-gray-600">Settings</p>
              </div>
            </button>
            <button className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-orange-500 hover:bg-orange-50 transition-colors">
              <div className="text-center">
                <svg className="w-8 h-8 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-gray-600">Help</p>
              </div>
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
