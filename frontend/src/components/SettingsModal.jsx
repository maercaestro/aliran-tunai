import { useState, useEffect } from 'react'

function SettingsModal({ isOpen, onClose, user, onUserUpdate, authToken }) {
  const [activeTab, setActiveTab] = useState('profile')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  const [profileData, setProfileData] = useState({
    owner_name: '',
    company_name: '',
    location: '',
    business_type: ''
  })

  useEffect(() => {
    if (user) {
      setProfileData({
        owner_name: user.owner_name || '',
        company_name: user.company_name || '',
        location: user.location || '',
        business_type: user.business_type || ''
      })
    }
  }, [user])

  const handleProfileChange = (e) => {
    const { name, value } = e.target
    setProfileData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleProfileUpdate = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const response = await fetch('https://api.aliran-tunai.com/api/user/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(profileData)
      })

      const data = await response.json()

      if (response.ok) {
        setSuccess('Profile updated successfully!')
        onUserUpdate({ ...user, ...profileData })
        setTimeout(() => setSuccess(''), 3000)
      } else {
        setError(data.error || 'Failed to update profile')
      }
    } catch (err) {
      setError('Connection error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleDataExport = async (format) => {
    setLoading(true)
    setError('')

    try {
      const response = await fetch(`https://api.aliran-tunai.com/api/download-excel/${user.wa_id}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `transactions_${user.company_name || user.wa_id}_${new Date().toISOString().split('T')[0]}.xlsx`
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        setSuccess(`Data exported successfully!`)
        setTimeout(() => setSuccess(''), 3000)
      } else {
        const errorData = await response.json()
        setError(errorData.error || 'Export failed')
      }
    } catch (err) {
      setError('Failed to export data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="neuro-card w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-[#424242]">Settings</h2>
            <button
              onClick={onClose}
              className="text-[#BDBDBD] hover:text-[#424242] text-xl font-bold"
            >
              ×
            </button>
          </div>

          {/* Tabs */}
          <div className="flex space-x-1 mb-6 neuro-card-inset p-1" style={{background: '#F5F5F5'}}>
            {[
              { id: 'profile', label: '👤 Profile', icon: '👤' },
              { id: 'whatsapp', label: '💬 WhatsApp', icon: '💬' },
              { id: 'data', label: '📊 Data', icon: '📊' },
              { id: 'app', label: '⚙️ App', icon: '⚙️' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 py-2 px-3 rounded text-sm font-medium transition-all ${
                  activeTab === tab.id 
                    ? 'neuro-button text-[#424242]' 
                    : 'text-[#BDBDBD] hover:text-[#424242]'
                }`}
              >
                <span className="hidden sm:inline">{tab.label}</span>
                <span className="sm:hidden">{tab.icon}</span>
              </button>
            ))}
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-600 text-sm">{success}</p>
            </div>
          )}

          {/* Tab Content */}
          <div className="space-y-6">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <form onSubmit={handleProfileUpdate} className="space-y-4">
                <h3 className="text-lg font-semibold text-[#424242] mb-4">Profile Information</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[#424242] mb-2">
                      Owner Name
                    </label>
                    <input
                      type="text"
                      name="owner_name"
                      value={profileData.owner_name}
                      onChange={handleProfileChange}
                      className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                      style={{background: '#F5F5F5'}}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-[#424242] mb-2">
                      Company Name
                    </label>
                    <input
                      type="text"
                      name="company_name"
                      value={profileData.company_name}
                      onChange={handleProfileChange}
                      className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                      style={{background: '#F5F5F5'}}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-[#424242] mb-2">
                      Location
                    </label>
                    <input
                      type="text"
                      name="location"
                      value={profileData.location}
                      onChange={handleProfileChange}
                      className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                      style={{background: '#F5F5F5'}}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-[#424242] mb-2">
                      Business Type
                    </label>
                    <input
                      type="text"
                      name="business_type"
                      value={profileData.business_type}
                      onChange={handleProfileChange}
                      className="neuro-card-inset w-full px-3 py-2 text-[#424242] border-none outline-none"
                      style={{background: '#F5F5F5'}}
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="neuro-button px-6 py-2 text-[#424242] font-medium disabled:opacity-50"
                >
                  {loading ? 'Updating...' : 'Update Profile'}
                </button>
              </form>
            )}

            {/* WhatsApp Tab */}
            {activeTab === 'whatsapp' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-[#424242] mb-4">WhatsApp Connection</h3>
                
                <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-[#424242] font-medium">Connected</span>
                  </div>
                  <p className="text-sm text-[#BDBDBD] mb-2">
                    Phone: +{user?.wa_id}
                  </p>
                  <p className="text-sm text-[#BDBDBD]">
                    You can add transactions by sending messages to the WhatsApp bot.
                  </p>
                </div>

                <div className="space-y-3">
                  <h4 className="font-semibold text-[#424242]">Quick Commands:</h4>
                  <div className="space-y-2 text-sm">
                    <div className="neuro-card-inset p-3" style={{background: '#F5F5F5'}}>
                      <code className="text-[#2196F3]">Sold 10 items for RM 150 each</code>
                      <p className="text-[#BDBDBD] mt-1">Record a sale</p>
                    </div>
                    <div className="neuro-card-inset p-3" style={{background: '#F5F5F5'}}>
                      <code className="text-[#2196F3]">Bought materials for RM 500</code>
                      <p className="text-[#BDBDBD] mt-1">Record a purchase</p>
                    </div>
                    <div className="neuro-card-inset p-3" style={{background: '#F5F5F5'}}>
                      <code className="text-[#2196F3]">Received payment RM 300 from Ali</code>
                      <p className="text-[#BDBDBD] mt-1">Record payment received</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Data Tab */}
            {activeTab === 'data' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-[#424242] mb-4">Data Management</h3>
                
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-[#424242] mb-3">Export Data</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <button
                        onClick={() => handleDataExport('excel')}
                        disabled={loading}
                        className="neuro-button p-4 text-left disabled:opacity-50"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                            <span className="text-green-600">📊</span>
                          </div>
                          <div>
                            <p className="font-medium text-[#424242]">Excel Export</p>
                            <p className="text-sm text-[#BDBDBD]">Download as .xlsx</p>
                          </div>
                        </div>
                      </button>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-[#424242] mb-3">Data Summary</h4>
                    <div className="neuro-card-inset p-4 space-y-2" style={{background: '#F5F5F5'}}>
                      <div className="flex justify-between">
                        <span className="text-[#BDBDBD]">Account Created:</span>
                        <span className="text-[#424242]">
                          {user?.registered_at ? new Date(user.registered_at).toLocaleDateString() : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#BDBDBD]">Phone Number:</span>
                        <span className="text-[#424242]">+{user?.wa_id}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* App Tab */}
            {activeTab === 'app' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-[#424242] mb-4">App Preferences</h3>
                
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-[#424242] mb-3">Version Information</h4>
                    <div className="neuro-card-inset p-4 space-y-2" style={{background: '#F5F5F5'}}>
                      <div className="flex justify-between">
                        <span className="text-[#BDBDBD]">App Version:</span>
                        <span className="text-[#424242]">1.0.0</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#BDBDBD]">Last Updated:</span>
                        <span className="text-[#424242]">October 2025</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-[#424242] mb-3">Support</h4>
                    <div className="space-y-2">
                      <button className="neuro-button w-full p-3 text-left">
                        <div className="flex items-center space-x-3">
                          <span className="text-[#4CAF50]">📧</span>
                          <span className="text-[#424242]">Contact Support</span>
                        </div>
                      </button>
                      <button className="neuro-button w-full p-3 text-left">
                        <div className="flex items-center space-x-3">
                          <span className="text-[#2196F3]">🔄</span>
                          <span className="text-[#424242]">Check for Updates</span>
                        </div>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsModal