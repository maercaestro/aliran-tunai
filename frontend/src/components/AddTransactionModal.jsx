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
    { value: 'sale', label: '💰 Sale', color: 'text-green-600' },
    { value: 'purchase', label: '🛒 Purchase', color: 'text-blue-600' },
    { value: 'expense', label: '💸 Expense', color: 'text-red-600' },
    { value: 'payment_received', label: '💵 Payment Received', color: 'text-green-600' },
    { value: 'payment_made', label: '💳 Payment Made', color: 'text-red-600' }
  ]

  const paymentMethods = [
    { value: 'cash', label: '💵 Cash' },
    { value: 'card', label: '💳 Card' },
    { value: 'bank_transfer', label: '🏦 Bank Transfer' },
    { value: 'ewallet', label: '📱 E-Wallet' },
    { value: 'check', label: '📝 Check' }
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="neuro-card w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-[#424242]">Add Transaction</h2>
            <button
              onClick={onClose}
              className="text-[#BDBDBD] hover:text-[#424242] text-xl font-bold"
            >
              ×
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Transaction Type */}
            <div>
              <label className="block text-sm font-medium text-[#424242] mb-2">
                Transaction Type
              </label>
              <select
                name="type"
                value={formData.type}
                onChange={handleInputChange}
                className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                style={{background: '#F5F5F5'}}
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
              <label className="block text-sm font-medium text-[#424242] mb-2">
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
                className="neuro-card-inset w-full px-3 py-2 text-[#424242] placeholder-[#BDBDBD] border-none outline-none"
                style={{background: '#F5F5F5'}}
                required
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-[#424242] mb-2">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                placeholder="What was this transaction for?"
                rows="3"
                className="neuro-card-inset w-full px-3 py-2 text-[#424242] placeholder-[#BDBDBD] border-none outline-none resize-none"
                style={{background: '#F5F5F5'}}
                required
              />
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-[#424242] mb-2">
                Category (Optional)
              </label>
              <input
                type="text"
                name="category"
                value={formData.category}
                onChange={handleInputChange}
                placeholder="e.g., Office Supplies, Inventory, Marketing"
                className="neuro-card-inset w-full px-3 py-2 text-[#424242] placeholder-[#BDBDBD] border-none outline-none"
                style={{background: '#F5F5F5'}}
              />
            </div>

            {/* Payment Method */}
            <div>
              <label className="block text-sm font-medium text-[#424242] mb-2">
                Payment Method
              </label>
              <select
                name="paymentMethod"
                value={formData.paymentMethod}
                onChange={handleInputChange}
                className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                style={{background: '#F5F5F5'}}
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
              <label className="block text-sm font-medium text-[#424242] mb-2">
                Date
              </label>
              <input
                type="date"
                name="date"
                value={formData.date}
                onChange={handleInputChange}
                className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                style={{background: '#F5F5F5'}}
              />
            </div>

            {/* Receipt Upload */}
            <div>
              <label className="block text-sm font-medium text-[#424242] mb-2">
                Receipt (Optional)
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none file:mr-4 file:py-1 file:px-2 file:rounded file:border-none file:text-sm file:bg-[#4CAF50] file:text-white"
                style={{background: '#F5F5F5'}}
              />
              {formData.receipt && (
                <p className="text-xs text-[#4CAF50] mt-1">
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
                className="flex-1 neuro-button-inset py-3 text-[#BDBDBD] font-medium disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 neuro-button py-3 text-[#424242] font-medium disabled:opacity-50"
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