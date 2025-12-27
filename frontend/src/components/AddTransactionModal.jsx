import { useState } from 'react'

function AddTransactionModal({ isOpen, onClose, onSubmit, user }) {
  const [formData, setFormData] = useState({
    type: 'sale', // sale, purchase, expense, payment_received, payment_made
    amount: '',
    description: '',
    category: '',
    paymentMethod: 'cash',
    date: new Date().toISOString().split('T')[0],
    receipt: null
  })
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const transactionTypes = [
    { value: 'sale', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" /></svg> Sale', color: 'text-green-600' },
    { value: 'purchase', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg> Purchase', color: 'text-blue-600' },
    { value: 'expense', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" /></svg> Expense', color: 'text-red-600' },
    { value: 'payment_received', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" /></svg> Payment Received', color: 'text-green-600' },
    { value: 'payment_made', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" /></svg> Payment Made', color: 'text-red-600' }
  ]

  const paymentMethods = [
    { value: 'cash', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" /></svg> Cash' },
    { value: 'card', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg> Card' },
    { value: 'bank_transfer', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg> Bank Transfer' },
    { value: 'ewallet', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg> E-Wallet' },
    { value: 'check', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> Check' }
  ]

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('File size must be less than 5MB')
        return
      }
      
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Please select an image file')
        return
      }

      setFormData(prev => ({
        ...prev,
        receipt: file
      }))
      setError('')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Validation
    if (!formData.amount || !formData.description) {
      setError('Amount and description are required')
      return
    }

    if (isNaN(formData.amount) || parseFloat(formData.amount) <= 0) {
      setError('Please enter a valid amount')
      return
    }

    setLoading(true)
    setError('')

    try {
      // Create form data for submission
      const submitData = {
        ...formData,
        amount: parseFloat(formData.amount),
        user_id: user.wa_id
      }

      await onSubmit(submitData)
      
      // Reset form
      setFormData({
        type: 'sale',
        amount: '',
        description: '',
        category: '',
        paymentMethod: 'cash',
        date: new Date().toISOString().split('T')[0],
        receipt: null
      })
      
      onClose()
    } catch (err) {
      setError(err.message || 'Failed to add transaction')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-[#10213C] border border-white/10 rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-white">Add Transaction</h2>
            <button
              onClick={onClose}
              className="text-[#B0B8C3] hover:text-white text-xl font-bold transition-colors"
            >
              ×
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Transaction Type */}
            <div>
              <label className="block text-sm font-medium text-[#B0B8C3] mb-2">
                Transaction Type
              </label>
              <select
                name="type"
                value={formData.type}
                onChange={handleInputChange}
                className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-lg text-white focus:border-[#00F0B5] outline-none transition-colors"
              >
                {transactionTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Amount */}
            <div>
              <label className="block text-sm font-medium text-[#B0B8C3] mb-2">
                Amount (RM)
              </label>
              <input
                type="number"
                name="amount"
                value={formData.amount}
                onChange={handleInputChange}
                placeholder="0.00"
                step="0.01"
                min="0"
                className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-lg text-white placeholder-[#B0B8C3]/50 focus:border-[#00F0B5] outline-none transition-colors"
                required
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-[#B0B8C3] mb-2">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                placeholder="What was this transaction for?"
                rows="3"
                className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-lg text-white placeholder-[#B0B8C3]/50 focus:border-[#00F0B5] outline-none transition-colors resize-none"
                required
              />
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-[#B0B8C3] mb-2">
                Category (Optional)
              </label>
              <input
                type="text"
                name="category"
                value={formData.category}
                onChange={handleInputChange}
                placeholder="e.g., Office Supplies, Inventory, Marketing"
                className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-lg text-white placeholder-[#B0B8C3]/50 focus:border-[#00F0B5] outline-none transition-colors"
              />
            </div>

            {/* Payment Method */}
            <div>
              <label className="block text-sm font-medium text-[#B0B8C3] mb-2">
                Payment Method
              </label>
              <select
                name="paymentMethod"
                value={formData.paymentMethod}
                onChange={handleInputChange}
                className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-lg text-white focus:border-[#00F0B5] outline-none transition-colors"
              >
                {paymentMethods.map(method => (
                  <option key={method.value} value={method.value}>
                    {method.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Date */}
            <div>
              <label className="block text-sm font-medium text-[#B0B8C3] mb-2">
                Date
              </label>
              <input
                type="date"
                name="date"
                value={formData.date}
                onChange={handleInputChange}
                className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-lg text-white focus:border-[#00F0B5] outline-none transition-colors"
              />
            </div>

            {/* Receipt Upload */}
            <div>
              <label className="block text-sm font-medium text-[#B0B8C3] mb-2">
                Receipt (Optional)
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-lg text-white file:mr-4 file:py-1 file:px-3 file:rounded-lg file:border-none file:text-sm file:bg-[#00F0B5] file:text-[#0A192F] file:font-medium file:cursor-pointer"
              />
              {formData.receipt && (
                <p className="text-xs text-[#00F0B5] mt-1">
                  ✅ {formData.receipt.name}
                </p>
              )}
            </div>

            {/* Submit Buttons */}
            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="flex-1 py-3 rounded-lg border border-white/10 text-[#B0B8C3] hover:bg-white/5 transition-colors font-medium disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-3 rounded-lg bg-[#00F0B5] text-[#0A192F] font-bold hover:bg-[#00F0B5]/90 transition-colors disabled:opacity-50"
              >
                {loading ? 'Adding...' : 'Add Transaction'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default AddTransactionModal