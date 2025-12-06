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
  const [activeTab, setActiveTab] = useState('all') // 'all', 'purchase', or 'sale'
  const [showExportMenu, setShowExportMenu] = useState(false)

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

  // Close export menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showExportMenu && !event.target.closest('.export-menu-container')) {
        setShowExportMenu(false)
      }
    }

    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [showExportMenu])

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

  const handleDownloadExcel = async (type = 'all') => {
    try {
      let endpoint
      let filename
      
      switch (type) {
        case 'purchase':
          endpoint = `${API_ENDPOINTS.DOWNLOAD_EXCEL(user.wa_id)}/purchase`
          filename = `purchase_transactions_${user.wa_id}_${new Date().getFullYear()}.xlsx`
          break
        case 'sale':
          endpoint = `${API_ENDPOINTS.DOWNLOAD_EXCEL(user.wa_id)}/sale`
          filename = `sale_transactions_${user.wa_id}_${new Date().getFullYear()}.xlsx`
          break
        default:
          endpoint = API_ENDPOINTS.DOWNLOAD_EXCEL(user.wa_id)
          filename = `transactions_${user.wa_id}_${new Date().getFullYear()}.xlsx`
      }

      const response = await fetch(buildApiUrl(endpoint), {
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
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        const data = await response.json()
        setError(data.error || `Failed to download ${type} Excel file`)
      }
    } catch (err) {
      setError(`Failed to export ${type} data`)
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
      case 'sale': return 'text-[#00F0B5] bg-[#00F0B5]/10'
      case 'purchase': return 'text-[#2196F3] bg-[#2196F3]/10'
      case 'expense': return 'text-red-400 bg-red-400/10'
      case 'payment_received': return 'text-[#00F0B5] bg-[#00F0B5]/10'
      case 'payment_made': return 'text-red-400 bg-red-400/10'
      default: return 'text-[#B0B8C3] bg-white/5'
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
      <div className="w-full min-h-screen flex items-center justify-center bg-[#0A192F]">
        <div className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#00F0B5] mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading transactions...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full min-h-screen bg-[#0A192F]">
      {/* Header */}
      <header className="relative z-10 bg-[#10213C]/60 backdrop-blur-xl border-b border-white/10 mb-6">
        <div className="p-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <button
                onClick={onBack}
                className="w-10 h-10 flex items-center justify-center bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all"
              >
                <svg className="w-5 h-5 text-[#B0B8C3]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div>
                <h1 className="text-2xl font-bold text-white">Transaction Reports</h1>
                <p className="text-[#B0B8C3] text-sm">View, edit, and export your transaction data</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={fetchTransactions}
                disabled={loading}
                className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-[#B0B8C3] hover:text-white transition-all disabled:opacity-50 flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Refresh</span>
              </button>
              <div className="relative export-menu-container">
                <button
                  onClick={() => setShowExportMenu(!showExportMenu)}
                  className="px-4 py-2 bg-[#00F0B5]/10 hover:bg-[#00F0B5]/20 border border-[#00F0B5]/30 rounded-xl text-[#00F0B5] flex items-center space-x-2 transition-all"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <span>Export Excel</span>
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                
                {showExportMenu && (
                  <div className="absolute right-0 top-full mt-2 w-48 bg-[#10213C] border border-white/10 rounded-xl py-2 z-50 shadow-2xl">
                    <button
                      onClick={() => {
                        handleDownloadExcel('all')
                        setShowExportMenu(false)
                      }}
                      className="w-full text-left px-4 py-2 text-[#B0B8C3] hover:text-white hover:bg-white/5 flex items-center space-x-2 transition-all"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span>All Transactions</span>
                    </button>
                    <button
                      onClick={() => {
                        handleDownloadExcel('purchase')
                        setShowExportMenu(false)
                      }}
                      className="w-full text-left px-4 py-2 text-[#B0B8C3] hover:text-white hover:bg-white/5 flex items-center space-x-2 transition-all"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                      </svg>
                      <span>Purchase Only</span>
                    </button>
                    <button
                      onClick={() => {
                        handleDownloadExcel('sale')
                        setShowExportMenu(false)
                      }}
                      className="w-full text-left px-4 py-2 text-[#B0B8C3] hover:text-white hover:bg-white/5 flex items-center space-x-2 transition-all"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                      </svg>
                      <span>Sale Only</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="px-6 pb-6">
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-xl">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Filters */}
        <div className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-4 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-[#B0B8C3] mb-2">Date From</label>
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => setFilters(prev => ({ ...prev, dateFrom: e.target.value }))}
                className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-xl text-white outline-none focus:border-[#00F0B5]/50 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#B0B8C3] mb-2">Date To</label>
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) => setFilters(prev => ({ ...prev, dateTo: e.target.value }))}
                className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-xl text-white outline-none focus:border-[#00F0B5]/50 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#B0B8C3] mb-2">Type</label>
              <select
                value={filters.type}
                onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value }))}
                className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-xl text-white outline-none focus:border-[#00F0B5]/50 transition-all"
              >
                {transactionTypes.map(type => (
                  <option key={type.value} value={type.value} className="bg-[#0A192F]">{type.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-[#B0B8C3] mb-2">Search</label>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                placeholder="Search descriptions, vendors..."
                className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-xl text-white placeholder-[#B0B8C3]/50 outline-none focus:border-[#00F0B5]/50 transition-all"
              />
            </div>
          </div>
        </div>

        {/* Transaction Type Toggle */}
        <div className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-4 mb-6">
          <div className="flex space-x-2">
            <button
              onClick={() => setActiveTab('all')}
              className={`px-6 py-2 rounded-xl font-medium transition-all ${
                activeTab === 'all' 
                  ? 'bg-[#2196F3] text-white shadow-[0_0_15px_rgba(33,150,243,0.3)]' 
                  : 'bg-white/5 text-[#B0B8C3] hover:text-white hover:bg-white/10'
              }`}
            >
              All Transactions
            </button>
            <button
              onClick={() => setActiveTab('purchase')}
              className={`px-6 py-2 rounded-xl font-medium transition-all ${
                activeTab === 'purchase' 
                  ? 'bg-orange-500 text-white shadow-[0_0_15px_rgba(249,115,22,0.3)]' 
                  : 'bg-white/5 text-[#B0B8C3] hover:text-white hover:bg-white/10'
              }`}
            >
              Purchase
            </button>
            <button
              onClick={() => setActiveTab('sale')}
              className={`px-6 py-2 rounded-xl font-medium transition-all ${
                activeTab === 'sale' 
                  ? 'bg-[#00F0B5] text-[#0A192F] shadow-[0_0_15px_rgba(0,240,181,0.3)]' 
                  : 'bg-white/5 text-[#B0B8C3] hover:text-white hover:bg-white/10'
              }`}
            >
              Sale
            </button>
          </div>
        </div>

        {/* Transactions Table */}
        <div className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left p-4 text-white font-semibold">
                    <button
                      onClick={() => handleSort('timestamp')}
                      className="flex items-center space-x-1 hover:text-[#00F0B5] transition-colors"
                    >
                      <span>Date</span>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                      </svg>
                    </button>
                  </th>
                  <th className="text-left p-4 text-white font-semibold">Type</th>
                  <th className="text-left p-4 text-white font-semibold">
                    <button
                      onClick={() => handleSort('amount')}
                      className="flex items-center space-x-1 hover:text-[#00F0B5] transition-colors"
                    >
                      <span>Amount</span>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                      </svg>
                    </button>
                  </th>
                  <th className="text-left p-4 text-white font-semibold">Description</th>
                  <th className="text-left p-4 text-white font-semibold">Vendor/Customer</th>
                  {activeTab === 'purchase' && (
                    <th className="text-left p-4 text-white font-semibold">Category</th>
                  )}
                  <th className="text-left p-4 text-white font-semibold">Payment</th>
                  <th className="text-center p-4 text-white font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.map((transaction) => (
                  <tr key={transaction._id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="p-4 text-[#B0B8C3]">
                      {new Date(transaction.timestamp).toLocaleDateString()}
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTransactionTypeColor(transaction.action)}`}>
                        {transaction.action}
                      </span>
                    </td>
                    <td className="p-4 text-white font-semibold">
                      {formatCurrency(transaction.amount)}
                    </td>
                    <td className="p-4 text-[#B0B8C3] max-w-xs truncate">
                      {transaction.description}
                    </td>
                    <td className="p-4 text-[#B0B8C3]/70">
                      {transaction.vendor || '-'}
                    </td>
                    {activeTab === 'purchase' && (
                      <td className="p-4">
                        {transaction.category ? (
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            purchaseCategories.find(cat => cat.value === transaction.category)?.color || 'bg-white/10 text-[#B0B8C3]'
                          }`}>
                            {transaction.category}
                          </span>
                        ) : (
                          <span className="px-2 py-1 rounded-full text-xs bg-yellow-500/10 text-yellow-400">
                            Uncategorized
                          </span>
                        )}
                      </td>
                    )}
                    <td className="p-4 text-[#B0B8C3]/70">
                      {transaction.terms || '-'}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center justify-center space-x-2">
                        {transaction.action === 'purchase' && !transaction.category && (
                          <button
                            onClick={() => handleCategorize(transaction)}
                            className="text-orange-400 hover:text-orange-300 p-1 transition-colors"
                            title="AI Categorize"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                          </button>
                        )}
                        <button
                          onClick={() => handleEdit(transaction)}
                          className="text-[#2196F3] hover:text-[#64B5F6] p-1 transition-colors"
                          title="Edit"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDelete(transaction._id)}
                          className="text-red-400 hover:text-red-300 p-1 transition-colors"
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
                <div className="text-[#B0B8C3]/50 mb-4">
                  <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">No transactions found</h3>
                <p className="text-[#B0B8C3]">
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
          <div className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-4 mt-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-white">{filteredTransactions.length}</div>
                <div className="text-sm text-[#B0B8C3]">Total Transactions</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-[#00F0B5]">
                  {formatCurrency(
                    filteredTransactions
                      .filter(t => ['sale', 'payment_received'].includes(t.action))
                      .reduce((sum, t) => sum + (t.amount || 0), 0)
                  )}
                </div>
                <div className="text-sm text-[#B0B8C3]">Total Income</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-400">
                  {formatCurrency(
                    filteredTransactions
                      .filter(t => ['purchase', 'expense', 'payment_made'].includes(t.action))
                      .reduce((sum, t) => sum + (t.amount || 0), 0)
                  )}
                </div>
                <div className="text-sm text-[#B0B8C3]">Total Expenses</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-white">
                  {formatCurrency(
                    filteredTransactions
                      .filter(t => ['sale', 'payment_received'].includes(t.action))
                      .reduce((sum, t) => sum + (t.amount || 0), 0) -
                    filteredTransactions
                      .filter(t => ['purchase', 'expense', 'payment_made'].includes(t.action))
                      .reduce((sum, t) => sum + (t.amount || 0), 0)
                  )}
                </div>
                <div className="text-sm text-[#B0B8C3]">Net Amount</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {editingTransaction && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#10213C] border border-white/10 rounded-2xl w-full max-w-md shadow-2xl">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-white">Edit Transaction</h3>
                <button
                  onClick={() => setEditingTransaction(null)}
                  className="text-[#B0B8C3] hover:text-white transition-colors"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[#B0B8C3] mb-2">Amount</label>
                  <input
                    type="number"
                    value={editingTransaction.amount}
                    onChange={(e) => setEditingTransaction(prev => ({ ...prev, amount: e.target.value }))}
                    className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-xl text-white outline-none focus:border-[#00F0B5]/50 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#B0B8C3] mb-2">Description</label>
                  <textarea
                    value={editingTransaction.description}
                    onChange={(e) => setEditingTransaction(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-xl text-white outline-none focus:border-[#00F0B5]/50 transition-all resize-none"
                    rows="3"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#B0B8C3] mb-2">Vendor/Customer</label>
                  <input
                    type="text"
                    value={editingTransaction.vendor || ''}
                    onChange={(e) => setEditingTransaction(prev => ({ ...prev, vendor: e.target.value }))}
                    className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-xl text-white outline-none focus:border-[#00F0B5]/50 transition-all"
                  />
                </div>

                {editingTransaction.action === 'purchase' && (
                  <div>
                    <label className="block text-sm font-medium text-[#B0B8C3] mb-2">Category</label>
                    <select
                      value={editingTransaction.category || ''}
                      onChange={(e) => setEditingTransaction(prev => ({ ...prev, category: e.target.value }))}
                      className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-xl text-white outline-none focus:border-[#00F0B5]/50 transition-all"
                    >
                      <option value="" className="bg-[#0A192F]">Select Category</option>
                      {purchaseCategories.map(category => (
                        <option key={category.value} value={category.value} className="bg-[#0A192F]">
                          {category.label}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-[#B0B8C3] mb-2">Payment Method</label>
                  <input
                    type="text"
                    value={editingTransaction.terms || ''}
                    onChange={(e) => setEditingTransaction(prev => ({ ...prev, terms: e.target.value }))}
                    className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-xl text-white outline-none focus:border-[#00F0B5]/50 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#B0B8C3] mb-2">Date</label>
                  <input
                    type="date"
                    value={editingTransaction.date}
                    onChange={(e) => setEditingTransaction(prev => ({ ...prev, date: e.target.value }))}
                    className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-xl text-white outline-none focus:border-[#00F0B5]/50 transition-all"
                  />
                </div>

                <div className="flex space-x-3 pt-4">
                  <button
                    onClick={() => setEditingTransaction(null)}
                    className="flex-1 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-[#B0B8C3] hover:text-white transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveEdit}
                    className="flex-1 py-2 bg-[#00F0B5] hover:bg-[#00D4A0] rounded-xl text-[#0A192F] font-medium transition-all"
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