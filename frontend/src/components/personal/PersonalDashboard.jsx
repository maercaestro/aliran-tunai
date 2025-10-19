import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

function PersonalDashboard({ user, authToken, onLogout, onModeChange }) {
  const [dashboardData, setDashboardData] = useState({
    monthlyIncome: 0,
    monthlyExpenses: 0,
    remainingBudget: 0,
    savingsThisMonth: 0,
    categoryBreakdown: [],
    recentTransactions: [],
    budgetProgress: {}
  })
  const [loading, setLoading] = useState(true)
  const [currentMonth] = useState(new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' }))

  useEffect(() => {
    fetchPersonalData()
  }, [user, authToken])

  const fetchPersonalData = async () => {
    // TODO: Implement API call to get personal budget data
    // For now, using mock data
    setTimeout(() => {
      setDashboardData({
        monthlyIncome: 4500,
        monthlyExpenses: 2850,
        remainingBudget: 1650,
        savingsThisMonth: 650,
        categoryBreakdown: [
          { name: 'Food & Dining', spent: 480, budget: 600, color: 'bg-red-500' },
          { name: 'Transportation', spent: 180, budget: 300, color: 'bg-blue-500' },
          { name: 'Shopping', spent: 320, budget: 400, color: 'bg-purple-500' },
          { name: 'Bills & Utilities', spent: 450, budget: 450, color: 'bg-yellow-500' },
          { name: 'Entertainment', spent: 120, budget: 200, color: 'bg-green-500' }
        ],
        recentTransactions: [
          { id: 1, description: 'Grocery shopping', amount: -85, category: 'Food', date: '2025-10-20' },
          { id: 2, description: 'Salary deposit', amount: 4500, category: 'Income', date: '2025-10-19' },
          { id: 3, description: 'Coffee shop', amount: -12, category: 'Food', date: '2025-10-19' },
          { id: 4, description: 'Gas station', amount: -60, category: 'Transportation', date: '2025-10-18' }
        ]
      })
      setLoading(false)
    }, 500)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your dashboard...</p>
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
              <h1 className="text-2xl font-bold text-gray-900">Personal Budget Dashboard</h1>
              <p className="text-gray-600">{currentMonth}</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => onModeChange('business')}
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-lg hover:bg-gray-100"
              >
                Switch to Business
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
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100 text-green-600">
                💰
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Monthly Income</p>
                <p className="text-2xl font-bold text-gray-900">${dashboardData.monthlyIncome.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-red-100 text-red-600">
                💸
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Expenses</p>
                <p className="text-2xl font-bold text-gray-900">${dashboardData.monthlyExpenses.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-blue-100 text-blue-600">
                🎯
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Remaining Budget</p>
                <p className="text-2xl font-bold text-gray-900">${dashboardData.remainingBudget.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-purple-100 text-purple-600">
                🏦
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Savings This Month</p>
                <p className="text-2xl font-bold text-gray-900">${dashboardData.savingsThisMonth.toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Budget Progress */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">Budget Progress</h3>
                <Link 
                  to="/personal/budgets" 
                  className="text-indigo-600 hover:text-indigo-700 text-sm font-medium"
                >
                  Manage Budgets
                </Link>
              </div>
            </div>
            <div className="p-6">
              <div className="space-y-6">
                {dashboardData.categoryBreakdown.map((category, index) => {
                  const percentage = (category.spent / category.budget) * 100
                  return (
                    <div key={index}>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-900">{category.name}</span>
                        <span className="text-sm text-gray-500">
                          ${category.spent} / ${category.budget}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${category.color} ${percentage > 100 ? 'bg-red-500' : ''}`}
                          style={{ width: `${Math.min(percentage, 100)}%` }}
                        ></div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Recent Transactions */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">Recent Transactions</h3>
                <Link 
                  to="/personal/expenses" 
                  className="text-indigo-600 hover:text-indigo-700 text-sm font-medium"
                >
                  View All
                </Link>
              </div>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {dashboardData.recentTransactions.map((transaction) => (
                  <div key={transaction.id} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className={`w-2 h-2 rounded-full mr-3 ${
                        transaction.amount > 0 ? 'bg-green-500' : 'bg-red-500'
                      }`}></div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{transaction.description}</p>
                        <p className="text-xs text-gray-500">{transaction.category} • {transaction.date}</p>
                      </div>
                    </div>
                    <span className={`text-sm font-medium ${
                      transaction.amount > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {transaction.amount > 0 ? '+' : ''}${Math.abs(transaction.amount)}
                    </span>
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
            <Link 
              to="/personal/expenses"
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <span className="text-2xl mb-2">📊</span>
              <span className="text-sm font-medium text-gray-900">Track Expenses</span>
            </Link>
            <Link 
              to="/personal/budgets"
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <span className="text-2xl mb-2">🎯</span>
              <span className="text-sm font-medium text-gray-900">Set Budgets</span>
            </Link>
            <Link 
              to="/personal/goals"
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <span className="text-2xl mb-2">🏆</span>
              <span className="text-sm font-medium text-gray-900">Financial Goals</span>
            </Link>
            <Link 
              to="/personal/insights"
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <span className="text-2xl mb-2">📈</span>
              <span className="text-sm font-medium text-gray-900">View Insights</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PersonalDashboard