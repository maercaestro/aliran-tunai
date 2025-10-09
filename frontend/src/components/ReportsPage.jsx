import { useState, useEffect } from 'react'
import { buildApiUrl, API_ENDPOINTS } from '../config/api'

function ReportsPage({ user, authToken, onBack }) {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editingTransaction, setEditingTransaction] = useState(null)
  const [filters, setFilters] = useState({
    dateFrom: '',
    dateTo: '',
    type: '',
    search: ''
  })
  const [sortConfig, setSortConfig] = useState({
    key: 'timestamp',
    direction: 'desc'
  })
  const [activeTab, setActiveTab] = useState('sales') // 'sales' or 'purchases'

  const transactionTypes = [
    { value: '', label: 'All Types' },
    { value: 'sale', label: 'Sale' },
    { value: 'purchase', label: 'Purchase' },
    { value: 'expense', label: 'Expense' },
    { value: 'payment_received', label: 'Payment Received' },
    { value: 'payment_made', label: 'Payment Made' }
  ]

  const purchaseCategories = [
    { value: 'OPEX', label: 'OPEX - Operating Expenses', color: 'bg-red-100 text-red-700' },
    { value: 'CAPEX', label: 'CAPEX - Capital Expenses', color: 'bg-blue-100 text-blue-700' },
    { value: 'COGS', label: 'COGS - Cost of Goods Sold', color: 'bg-orange-100 text-orange-700' },
    { value: 'INVENTORY', label: 'Inventory Purchase', color: 'bg-green-100 text-green-700' },
    { value: 'MARKETING', label: 'Marketing & Advertising', color: 'bg-purple-100 text-purple-700' },
    { value: 'UTILITIES', label: 'Utilities & Overheads', color: 'bg-yellow-100 text-yellow-700' },
    { value: 'OTHER', label: 'Other', color: 'bg-gray-100 text-gray-700' }
  ]

  useEffect(() => {
    fetchTransactions()
  }, [])

  const fetchTransactions = async () => {
    try {
      setLoading(true)
      setError('')

      const response = await fetch(buildApiUrl(API_ENDPOINTS.USER_TRANSACTIONS(user.wa_id)), {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })

      const data = await response.json()

      if (response.ok) {
        setTransactions(data.transactions || [])
      } else {
        setError(data.error || 'Failed to fetch transactions')
      }
    } catch (err) {
      setError('Connection error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSort = (key) => {
    let direction = 'asc'
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc'
    }
    setSortConfig({ key, direction })
  }

  const handleEdit = (transaction) => {
    setEditingTransaction({
      ...transaction,
      date: transaction.timestamp ? new Date(transaction.timestamp).toISOString().split('T')[0] : '',
      amount: transaction.amount?.toString() || ''
    })
  }

  const handleSaveEdit = async () => {
    try {
      const response = await fetch(buildApiUrl(API_ENDPOINTS.TRANSACTION(editingTransaction._id)), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          action: editingTransaction.action,
          amount: parseFloat(editingTransaction.amount),
          description: editingTransaction.description,
          vendor: editingTransaction.vendor,
          terms: editingTransaction.terms,
          date: editingTransaction.date,
          category: editingTransaction.category || null
        })
      })

      const data = await response.json()

      if (response.ok) {
        // Update the transaction in the local state
        setTransactions(prev => 
          prev.map(t => t._id === editingTransaction._id ? data.transaction : t)
        )
        setEditingTransaction(null)
      } else {
        setError(data.error || 'Failed to update transaction')
      }
    } catch (err) {
      setError('Failed to update transaction')
    }
  }

  const handleDelete = async (transactionId) => {
    if (!confirm('Are you sure you want to delete this transaction?')) {
      return
    }

    try {
      const response = await fetch(buildApiUrl(API_ENDPOINTS.TRANSACTION(transactionId)), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })

      if (response.ok) {
        setTransactions(prev => prev.filter(t => t._id !== transactionId))
      } else {
        const data = await response.json()
        setError(data.error || 'Failed to delete transaction')
      }
    } catch (err) {
      setError('Failed to delete transaction')
    }
  }

  const handleCategorize = async (transaction) => {
    try {
      const response = await fetch(buildApiUrl('/api/categorize'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          description: transaction.description,
          vendor: transaction.vendor,
          amount: transaction.amount
        })
      })

      const data = await response.json()

      if (response.ok) {
        // Update the transaction with the suggested category
        const updatedTransaction = { ...transaction, category: data.category }
        setEditingTransaction(updatedTransaction)
      } else {
        setError(data.error || 'Failed to categorize transaction')
      }
    } catch (err) {
      setError('Failed to categorize transaction')
    }
  }

  const handleDownloadExcel = async () => {
    try {
      const response = await fetch(buildApiUrl(API_ENDPOINTS.DOWNLOAD_EXCEL(user.wa_id)), {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.style.display = 'none'
        a.href = url
        a.download = `transactions_${user.wa_id}_${new Date().getFullYear()}.xlsx`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        const data = await response.json()
        setError(data.error || 'Failed to download Excel file')
      }
    } catch (err) {
      setError('Failed to export data')
    }
  }  // Filter and sort transactions
  const filteredTransactions = transactions
    .filter(transaction => {
      // Tab filtering
      if (activeTab === 'purchase' && transaction.action !== 'purchase') return false
      if (activeTab === 'sale' && transaction.action !== 'sale') return false
      
      // Other filters
      if (filters.type && transaction.action !== filters.type) return false
      if (filters.search && !transaction.description?.toLowerCase().includes(filters.search.toLowerCase()) &&
          !transaction.vendor?.toLowerCase().includes(filters.search.toLowerCase())) return false
      if (filters.dateFrom && new Date(transaction.timestamp) < new Date(filters.dateFrom)) return false
      if (filters.dateTo && new Date(transaction.timestamp) > new Date(filters.dateTo)) return false
      return true
    })
    .sort((a, b) => {
      const aValue = a[sortConfig.key]
      const bValue = b[sortConfig.key]
      
      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1
      return 0
    })

  const getTransactionTypeColor = (type) => {
    switch (type) {
      case 'sale': return 'text-green-600 bg-green-50'
      case 'purchase': return 'text-blue-600 bg-blue-50'
      case 'expense': return 'text-red-600 bg-red-50'
      case 'payment_received': return 'text-green-600 bg-green-50'
      case 'payment_made': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ms-MY', {
      style: 'currency',
      currency: 'MYR'
    }).format(amount || 0)
  }

  if (loading) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center" style={{background: '#F5F5F5'}}>
        <div className="neuro-card p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#2196F3] mx-auto mb-4"></div>
          <p className="text-[#424242] text-lg">Loading transactions...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full min-h-screen" style={{
      background: 'linear-gradient(135deg, #F5F5F5 0%, #F8F9FA 20%, #F5F5F5 40%, rgba(76, 175, 80, 0.02) 60%, #F5F5F5 80%, rgba(255, 179, 0, 0.01) 100%)',
      backgroundSize: '400% 400%',
      animation: 'subtleShift 20s ease-in-out infinite'
    }}>
      {/* Header */}
      <header className="relative z-10 neuro-card mb-6">
        <div className="p-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <button
                onClick={onBack}
                className="neuro-button w-10 h-10 flex items-center justify-center"
              >
                <svg className="w-5 h-5 text-[#424242]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div>
                <h1 className="text-2xl font-bold text-[#424242]">Transaction Reports</h1>
                <p className="text-[#BDBDBD] text-sm">View, edit, and export your transaction data</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={fetchTransactions}
                disabled={loading}
                className="neuro-button px-4 py-2 text-[#424242] disabled:opacity-50"
              >
                🔄 Refresh
              </button>
              <button
                onClick={handleDownloadExcel}
                className="neuro-button px-4 py-2 text-[#424242] flex items-center space-x-2"
              >
                <span>📊</span>
                <span>Export Excel</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="px-6 pb-6">
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        )}

        {/* Filters */}
        <div className="neuro-card p-4 mb-6">
          <h3 className="text-lg font-semibold text-[#424242] mb-4">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-[#424242] mb-2">Date From</label>
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => setFilters(prev => ({ ...prev, dateFrom: e.target.value }))}
                className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                style={{background: '#F5F5F5'}}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#424242] mb-2">Date To</label>
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) => setFilters(prev => ({ ...prev, dateTo: e.target.value }))}
                className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                style={{background: '#F5F5F5'}}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#424242] mb-2">Type</label>
              <select
                value={filters.type}
                onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value }))}
                className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                style={{background: '#F5F5F5'}}
              >
                {transactionTypes.map(type => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-[#424242] mb-2">Search</label>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                placeholder="Search descriptions, vendors..."
                className="neuro-card-inset w-full px-3 py-2 text-[#424242] placeholder-[#BDBDBD] border-none outline-none"
                style={{background: '#F5F5F5'}}
              />
            </div>
          </div>
        </div>

        {/* Transaction Type Toggle */}
        <div className="neuro-card">
          <div className="flex space-x-2 mb-4">
            <button
              onClick={() => setActiveTab('all')}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                activeTab === 'all' 
                  ? 'bg-[#2196F3] text-white shadow-lg' 
                  : 'bg-[#F5F5F5] text-[#424242] hover:bg-[#EEEEEE]'
              }`}
            >
              All Transactions
            </button>
            <button
              onClick={() => setActiveTab('purchase')}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                activeTab === 'purchase' 
                  ? 'bg-[#FF9800] text-white shadow-lg' 
                  : 'bg-[#F5F5F5] text-[#424242] hover:bg-[#EEEEEE]'
              }`}
            >
              Purchase
            </button>
            <button
              onClick={() => setActiveTab('sale')}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                activeTab === 'sale' 
                  ? 'bg-[#4CAF50] text-white shadow-lg' 
                  : 'bg-[#F5F5F5] text-[#424242] hover:bg-[#EEEEEE]'
              }`}
            >
              Sale
            </button>
          </div>
        </div>

        {/* Transactions Table */}
        <div className="neuro-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#BDBDBD]/20">
                  <th className="text-left p-4 text-[#424242] font-semibold">
                    <button
                      onClick={() => handleSort('timestamp')}
                      className="flex items-center space-x-1 hover:text-[#2196F3]"
                    >
                      <span>Date</span>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                      </svg>
                    </button>
                  </th>
                  <th className="text-left p-4 text-[#424242] font-semibold">Type</th>
                  <th className="text-left p-4 text-[#424242] font-semibold">
                    <button
                      onClick={() => handleSort('amount')}
                      className="flex items-center space-x-1 hover:text-[#2196F3]"
                    >
                      <span>Amount</span>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                      </svg>
                    </button>
                  </th>
                  <th className="text-left p-4 text-[#424242] font-semibold">Description</th>
                  <th className="text-left p-4 text-[#424242] font-semibold">Vendor/Customer</th>
                  {activeTab === 'purchase' && (
                    <th className="text-left p-4 text-[#424242] font-semibold">Category</th>
                  )}
                  <th className="text-left p-4 text-[#424242] font-semibold">Payment</th>
                  <th className="text-center p-4 text-[#424242] font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.map((transaction) => (
                  <tr key={transaction._id} className="border-b border-[#BDBDBD]/10 hover:bg-[#F8F9FA]/50">
                    <td className="p-4 text-[#424242]">
                      {new Date(transaction.timestamp).toLocaleDateString()}
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTransactionTypeColor(transaction.action)}`}>
                        {transaction.action}
                      </span>
                    </td>
                    <td className="p-4 text-[#424242] font-semibold">
                      {formatCurrency(transaction.amount)}
                    </td>
                    <td className="p-4 text-[#424242] max-w-xs truncate">
                      {transaction.description}
                    </td>
                    <td className="p-4 text-[#BDBDBD]">
                      {transaction.vendor || '-'}
                    </td>
                    {activeTab === 'purchase' && (
                      <td className="p-4">
                        {transaction.category ? (
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            purchaseCategories.find(cat => cat.value === transaction.category)?.color || 'bg-gray-100 text-gray-700'
                          }`}>
                            {transaction.category}
                          </span>
                        ) : (
                          <span className="px-2 py-1 rounded-full text-xs bg-yellow-100 text-yellow-700">
                            Uncategorized
                          </span>
                        )}
                      </td>
                    )}
                    <td className="p-4 text-[#BDBDBD]">
                      {transaction.terms || '-'}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center justify-center space-x-2">
                        {transaction.action === 'purchase' && !transaction.category && (
                          <button
                            onClick={() => handleCategorize(transaction)}
                            className="text-[#FF9800] hover:text-[#F57C00] p-1"
                            title="AI Categorize"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                          </button>
                        )}
                        <button
                          onClick={() => handleEdit(transaction)}
                          className="text-[#2196F3] hover:text-[#1976D2] p-1"
                          title="Edit"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDelete(transaction._id)}
                          className="text-[#F44336] hover:text-[#D32F2F] p-1"
                          title="Delete"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {filteredTransactions.length === 0 && (
              <div className="text-center py-12">
                <div className="text-[#BDBDBD] text-6xl mb-4">📊</div>
                <h3 className="text-lg font-semibold text-[#424242] mb-2">No transactions found</h3>
                <p className="text-[#BDBDBD]">
                  {transactions.length === 0 
                    ? "Start adding transactions to see them here"
                    : "Try adjusting your filters"
                  }
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Summary */}
        {filteredTransactions.length > 0 && (
          <div className="neuro-card p-4 mt-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-[#424242]">{filteredTransactions.length}</div>
                <div className="text-sm text-[#BDBDBD]">Total Transactions</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {formatCurrency(
                    filteredTransactions
                      .filter(t => ['sale', 'payment_received'].includes(t.action))
                      .reduce((sum, t) => sum + (t.amount || 0), 0)
                  )}
                </div>
                <div className="text-sm text-[#BDBDBD]">Total Income</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-600">
                  {formatCurrency(
                    filteredTransactions
                      .filter(t => ['purchase', 'expense', 'payment_made'].includes(t.action))
                      .reduce((sum, t) => sum + (t.amount || 0), 0)
                  )}
                </div>
                <div className="text-sm text-[#BDBDBD]">Total Expenses</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-[#424242]">
                  {formatCurrency(
                    filteredTransactions
                      .filter(t => ['sale', 'payment_received'].includes(t.action))
                      .reduce((sum, t) => sum + (t.amount || 0), 0) -
                    filteredTransactions
                      .filter(t => ['purchase', 'expense', 'payment_made'].includes(t.action))
                      .reduce((sum, t) => sum + (t.amount || 0), 0)
                  )}
                </div>
                <div className="text-sm text-[#BDBDBD]">Net Amount</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {editingTransaction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="neuro-card w-full max-w-md">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-[#424242]">Edit Transaction</h3>
                <button
                  onClick={() => setEditingTransaction(null)}
                  className="text-[#BDBDBD] hover:text-[#424242]"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[#424242] mb-2">Amount</label>
                  <input
                    type="number"
                    value={editingTransaction.amount}
                    onChange={(e) => setEditingTransaction(prev => ({ ...prev, amount: e.target.value }))}
                    className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                    style={{background: '#F5F5F5'}}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#424242] mb-2">Description</label>
                  <textarea
                    value={editingTransaction.description}
                    onChange={(e) => setEditingTransaction(prev => ({ ...prev, description: e.target.value }))}
                    className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none resize-none"
                    style={{background: '#F5F5F5'}}
                    rows="3"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#424242] mb-2">Vendor/Customer</label>
                  <input
                    type="text"
                    value={editingTransaction.vendor || ''}
                    onChange={(e) => setEditingTransaction(prev => ({ ...prev, vendor: e.target.value }))}
                    className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                    style={{background: '#F5F5F5'}}
                  />
                </div>

                {editingTransaction.action === 'purchase' && (
                  <div>
                    <label className="block text-sm font-medium text-[#424242] mb-2">Category</label>
                    <select
                      value={editingTransaction.category || ''}
                      onChange={(e) => setEditingTransaction(prev => ({ ...prev, category: e.target.value }))}
                      className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                      style={{background: '#F5F5F5'}}
                    >
                      <option value="">Select Category</option>
                      {purchaseCategories.map(category => (
                        <option key={category.value} value={category.value}>
                          {category.label}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-[#424242] mb-2">Payment Method</label>
                  <input
                    type="text"
                    value={editingTransaction.terms || ''}
                    onChange={(e) => setEditingTransaction(prev => ({ ...prev, terms: e.target.value }))}
                    className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                    style={{background: '#F5F5F5'}}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#424242] mb-2">Date</label>
                  <input
                    type="date"
                    value={editingTransaction.date}
                    onChange={(e) => setEditingTransaction(prev => ({ ...prev, date: e.target.value }))}
                    className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                    style={{background: '#F5F5F5'}}
                  />
                </div>

                <div className="flex space-x-3 pt-4">
                  <button
                    onClick={() => setEditingTransaction(null)}
                    className="flex-1 neuro-button-inset py-2 text-[#BDBDBD]"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveEdit}
                    className="flex-1 neuro-button py-2 text-[#424242] font-medium"
                  >
                    Save Changes
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ReportsPage