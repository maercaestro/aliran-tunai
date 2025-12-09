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
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-[#10213C] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-white">Settings</h2>
            <button
              onClick={onClose}
              className="text-[#B0B8C3] hover:text-white text-xl font-bold transition-colors"
            >
              ×
            </button>
          </div>

          {/* Tabs */}
          <div className="flex space-x-1 mb-6 bg-[#0A192F]/50 border border-white/10 rounded-xl p-1">
            {[
              { id: 'profile', label: '<svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg> Profile', icon: '<svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>' },
              { id: 'whatsapp', label: '<svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg> WhatsApp', icon: '<svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>' },
              { id: 'data', label: '<svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg> Data', icon: '<svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>' },
              { id: 'app', label: '<svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg> App', icon: '<svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.id 
                    ? 'bg-[#00F0B5] text-[#0A192F]' 
                    : 'text-[#B0B8C3] hover:text-white hover:bg-white/5'
                }`}
              >
                <span className="hidden sm:inline" dangerouslySetInnerHTML={{ __html: tab.label }}></span>
                <span className="sm:hidden" dangerouslySetInnerHTML={{ __html: tab.icon }}></span>
              </button>
            ))}
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-[#00F0B5]/10 border border-[#00F0B5]/20 rounded-lg">
              <p className="text-[#00F0B5] text-sm">{success}</p>
            </div>
          )}

          {/* Tab Content */}
          <div className="space-y-6">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <form onSubmit={handleProfileUpdate} className="space-y-4">
                <h3 className="text-lg font-semibold text-white mb-4">Profile Information</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[#B0B8C3] mb-2">
                      Owner Name
                    </label>
                    <input
                      type="text"
                      name="owner_name"
                      value={profileData.owner_name}
                      onChange={handleProfileChange}
                      className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-lg text-white focus:border-[#00F0B5] outline-none transition-colors"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-[#B0B8C3] mb-2">
                      Company Name
                    </label>
                    <input
                      type="text"
                      name="company_name"
                      value={profileData.company_name}
                      onChange={handleProfileChange}
                      className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-lg text-white focus:border-[#00F0B5] outline-none transition-colors"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-[#B0B8C3] mb-2">
                      Location
                    </label>
                    <input
                      type="text"
                      name="location"
                      value={profileData.location}
                      onChange={handleProfileChange}
                      className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-lg text-white focus:border-[#00F0B5] outline-none transition-colors"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-[#B0B8C3] mb-2">
                      Business Type
                    </label>
                    <input
                      type="text"
                      name="business_type"
                      value={profileData.business_type}
                      onChange={handleProfileChange}
                      className="w-full px-3 py-2 bg-[#0A192F]/50 border border-white/10 rounded-lg text-white focus:border-[#00F0B5] outline-none transition-colors"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2 rounded-lg bg-[#00F0B5] text-[#0A192F] font-bold hover:bg-[#00F0B5]/90 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Updating...' : 'Update Profile'}
                </button>
              </form>
            )}

            {/* WhatsApp Tab */}
            {activeTab === 'whatsapp' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white mb-4">WhatsApp Connection</h3>
                
                <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="w-3 h-3 bg-[#00F0B5] rounded-full animate-pulse shadow-[0_0_8px_#00F0B5]"></div>
                    <span className="text-white font-medium">Connected</span>
                  </div>
                  <p className="text-sm text-[#B0B8C3] mb-2">
                    Phone: +{user?.wa_id}
                  </p>
                  <p className="text-sm text-[#B0B8C3]">
                    You can add transactions by sending messages to the WhatsApp bot.
                  </p>
                </div>

                <div className="space-y-3">
                  <h4 className="font-semibold text-white">Quick Commands:</h4>
                  <div className="space-y-2 text-sm">
                    <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-3">
                      <code className="text-[#00F0B5]">Sold 10 items for RM 150 each</code>
                      <p className="text-[#B0B8C3] mt-1">Record a sale</p>
                    </div>
                    <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-3">
                      <code className="text-[#00F0B5]">Bought materials for RM 500</code>
                      <p className="text-[#B0B8C3] mt-1">Record a purchase</p>
                    </div>
                    <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-3">
                      <code className="text-[#00F0B5]">Received payment RM 300 from Ali</code>
                      <p className="text-[#B0B8C3] mt-1">Record payment received</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Data Tab */}
            {activeTab === 'data' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white mb-4">Data Management</h3>
                
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-white mb-3">Export Data</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <button
                        onClick={() => handleDataExport('excel')}
                        disabled={loading}
                        className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4 text-left hover:border-[#00F0B5]/50 transition-all disabled:opacity-50"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-[#00F0B5]/10 rounded-lg flex items-center justify-center">
                            <svg className="w-4 h-4 text-[#00F0B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                          </div>
                          <div>
                            <p className="font-medium text-white">Excel Export</p>
                            <p className="text-sm text-[#B0B8C3]">Download as .xlsx</p>
                          </div>
                        </div>
                      </button>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-white mb-3">Data Summary</h4>
                    <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4 space-y-2">
                      <div className="flex justify-between">
                        <span className="text-[#B0B8C3]">Account Created:</span>
                        <span className="text-white">
                          {user?.registered_at ? new Date(user.registered_at).toLocaleDateString() : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#B0B8C3]">Phone Number:</span>
                        <span className="text-white">+{user?.wa_id}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* App Tab */}
            {activeTab === 'app' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white mb-4">App Preferences</h3>
                
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-white mb-3">Version Information</h4>
                    <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4 space-y-2">
                      <div className="flex justify-between">
                        <span className="text-[#B0B8C3]">App Version:</span>
                        <span className="text-white">1.0.0</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#B0B8C3]">Last Updated:</span>
                        <span className="text-white">December 2025</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-white mb-3">Support</h4>
                    <div className="space-y-2">
                      <button className="w-full bg-[#0A192F]/50 border border-white/10 rounded-xl p-3 text-left hover:border-[#00F0B5]/50 transition-all">
                        <div className="flex items-center space-x-3">
                          <svg className="w-4 h-4 text-[#00F0B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                          <span className="text-white">Contact Support</span>
                        </div>
                      </button>
                      <button className="w-full bg-[#0A192F]/50 border border-white/10 rounded-xl p-3 text-left hover:border-[#00F0B5]/50 transition-all">
                        <div className="flex items-center space-x-3">
                          <svg className="w-4 h-4 text-[#2196F3]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          <span className="text-white">Check for Updates</span>
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