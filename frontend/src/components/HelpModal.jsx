import { useState } from 'react'

function HelpModal({ isOpen, onClose }) {
  const [activeSection, setActiveSection] = useState('getting-started')

  const helpSections = [
    { id: 'getting-started', label: '🚀 Getting Started', icon: '🚀' },
    { id: 'whatsapp', label: '💬 WhatsApp Bot', icon: '💬' },
    { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
    { id: 'faq', label: '❓ FAQ', icon: '❓' }
  ]

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="neuro-card w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-[#4CAF50] to-[#2196F3] rounded-lg flex items-center justify-center">
                <span className="text-white text-lg">❓</span>
              </div>
              <h2 className="text-xl font-bold text-[#424242]">Help & Support</h2>
            </div>
            <button
              onClick={onClose}
              className="text-[#BDBDBD] hover:text-[#424242] text-xl font-bold"
            >
              ×
            </button>
          </div>

          <div className="flex flex-col lg:flex-row gap-6">
            {/* Sidebar */}
            <div className="lg:w-1/4">
              <div className="neuro-card-inset p-3 space-y-2" style={{background: '#F5F5F5'}}>
                {helpSections.map(section => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full text-left p-3 rounded-lg transition-all ${
                      activeSection === section.id 
                        ? 'neuro-button text-[#424242] font-medium' 
                        : 'text-[#BDBDBD] hover:text-[#424242]'
                    }`}
                  >
                    <span className="lg:hidden">{section.icon}</span>
                    <span className="hidden lg:inline">{section.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Content */}
            <div className="lg:w-3/4">
              <div className="space-y-6">
                {/* Getting Started */}
                {activeSection === 'getting-started' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold text-[#424242] mb-4">🚀 Getting Started with AliranTunai</h3>
                      
                      <div className="space-y-4">
                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-2">1. WhatsApp Registration</h4>
                          <p className="text-[#BDBDBD] text-sm">
                            First, you need to register via WhatsApp by providing your business information:
                          </p>
                          <ul className="list-disc list-inside text-[#BDBDBD] text-sm mt-2 ml-4">
                            <li>Owner name</li>
                            <li>Company name</li>
                            <li>Location</li>
                            <li>Business type</li>
                          </ul>
                        </div>

                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-2">2. Dashboard Login</h4>
                          <p className="text-[#BDBDBD] text-sm">
                            After registration, you can access this dashboard using your phone number and OTP verification.
                          </p>
                        </div>

                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-2">3. Start Tracking</h4>
                          <p className="text-[#BDBDBD] text-sm">
                            You can add transactions either through WhatsApp messages or using the dashboard form.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* WhatsApp Bot */}
                {activeSection === 'whatsapp' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold text-[#424242] mb-4">💬 WhatsApp Bot Guide</h3>
                      
                      <div className="space-y-4">
                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-3">How to Record Transactions</h4>
                          <p className="text-[#BDBDBD] text-sm mb-3">
                            Simply send a message describing your transaction in natural language:
                          </p>
                          
                          <div className="space-y-3">
                            <div className="bg-green-50 p-3 rounded-lg border-l-4 border-green-500">
                              <p className="text-sm font-mono text-green-700">
                                "Sold 5 pieces of clothing for RM 50 each"
                              </p>
                              <p className="text-xs text-green-600 mt-1">→ Records RM 250 sale</p>
                            </div>
                            
                            <div className="bg-blue-50 p-3 rounded-lg border-l-4 border-blue-500">
                              <p className="text-sm font-mono text-blue-700">
                                "Bought inventory from supplier for RM 800"
                              </p>
                              <p className="text-xs text-blue-600 mt-1">→ Records RM 800 purchase</p>
                            </div>
                            
                            <div className="bg-orange-50 p-3 rounded-lg border-l-4 border-orange-500">
                              <p className="text-sm font-mono text-orange-700">
                                "Received payment RM 300 from customer Ali"
                              </p>
                              <p className="text-xs text-orange-600 mt-1">→ Records RM 300 payment received</p>
                            </div>
                          </div>
                        </div>

                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-3">Supported Transaction Types</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div className="flex items-center space-x-2">
                              <span className="text-green-600">💰</span>
                              <span className="text-sm text-[#424242]">Sales</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-blue-600">🛒</span>
                              <span className="text-sm text-[#424242]">Purchases</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-red-600">💸</span>
                              <span className="text-sm text-[#424242]">Expenses</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-green-600">💵</span>
                              <span className="text-sm text-[#424242]">Payments Received</span>
                            </div>
                          </div>
                        </div>

                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-3">Tips for Better Recognition</h4>
                          <ul className="space-y-2 text-sm text-[#BDBDBD]">
                            <li className="flex items-start space-x-2">
                              <span className="text-[#4CAF50] mt-0.5">✓</span>
                              <span>Include amounts in RM (Malaysian Ringgit)</span>
                            </li>
                            <li className="flex items-start space-x-2">
                              <span className="text-[#4CAF50] mt-0.5">✓</span>
                              <span>Use clear action words like "sold", "bought", "received", "paid"</span>
                            </li>
                            <li className="flex items-start space-x-2">
                              <span className="text-[#4CAF50] mt-0.5">✓</span>
                              <span>Mention quantities when applicable</span>
                            </li>
                            <li className="flex items-start space-x-2">
                              <span className="text-[#4CAF50] mt-0.5">✓</span>
                              <span>You can attach receipt images for better record keeping</span>
                            </li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Dashboard */}
                {activeSection === 'dashboard' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold text-[#424242] mb-4">📊 Dashboard Features</h3>
                      
                      <div className="space-y-4">
                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-3">Cash Conversion Cycle (CCC)</h4>
                          <p className="text-[#BDBDBD] text-sm mb-3">
                            The main metric showing how efficiently your business converts investments into cash flows.
                          </p>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                            <div className="text-center">
                              <div className="text-green-600 font-semibold">&lt; 30 days</div>
                              <div className="text-[#BDBDBD]">Excellent</div>
                            </div>
                            <div className="text-center">
                              <div className="text-blue-600 font-semibold">30-60 days</div>
                              <div className="text-[#BDBDBD]">Good</div>
                            </div>
                            <div className="text-center">
                              <div className="text-orange-600 font-semibold">60-90 days</div>
                              <div className="text-[#BDBDBD]">Moderate</div>
                            </div>
                            <div className="text-center">
                              <div className="text-red-600 font-semibold">&gt; 90 days</div>
                              <div className="text-[#BDBDBD]">Needs Attention</div>
                            </div>
                          </div>
                        </div>

                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-3">Financial Summary</h4>
                          <p className="text-[#BDBDBD] text-sm">
                            View your total sales, purchases, and cash flow at a glance. The summary updates automatically as you add new transactions.
                          </p>
                        </div>

                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-3">Recent Transactions</h4>
                          <p className="text-[#BDBDBD] text-sm">
                            See your latest business activities with details like amount, type, and date. Click the Excel button to download your complete transaction history.
                          </p>
                        </div>

                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-3">Quick Actions</h4>
                          <p className="text-[#BDBDBD] text-sm mb-3">
                            Use the buttons at the bottom to:
                          </p>
                          <ul className="space-y-1 text-sm text-[#BDBDBD] ml-4">
                            <li>• Add transactions manually</li>
                            <li>• Access settings and profile</li>
                            <li>• Get help and support</li>
                            <li>• View detailed reports</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* FAQ */}
                {activeSection === 'faq' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold text-[#424242] mb-4">❓ Frequently Asked Questions</h3>
                      
                      <div className="space-y-4">
                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-2">How do I register for AliranTunai?</h4>
                          <p className="text-[#BDBDBD] text-sm">
                            Send a message to our WhatsApp bot. You'll be guided through a 4-step registration process where you provide your owner name, company name, location, and business type.
                          </p>
                        </div>

                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-2">Is my data secure?</h4>
                          <p className="text-[#BDBDBD] text-sm">
                            Yes! Your data is stored securely in our encrypted database. Each user can only access their own data, and we use industry-standard security practices.
                          </p>
                        </div>

                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-2">Can I edit or delete transactions?</h4>
                          <p className="text-[#BDBDBD] text-sm">
                            Currently, transactions are recorded as permanent entries for audit purposes. If you made an error, you can add a correcting transaction or contact support.
                          </p>
                        </div>

                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-2">What happens if I lose access to my WhatsApp?</h4>
                          <p className="text-[#BDBDBD] text-sm">
                            Your data is tied to your phone number. If you change numbers, contact our support team to transfer your account.
                          </p>
                        </div>

                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-2">How can I export my data?</h4>
                          <p className="text-[#BDBDBD] text-sm">
                            Use the Excel export button in the dashboard header or go to Settings → Data → Export Data to download your complete transaction history.
                          </p>
                        </div>

                        <div className="neuro-card-inset p-4" style={{background: '#F5F5F5'}}>
                          <h4 className="font-semibold text-[#424242] mb-2">Need more help?</h4>
                          <p className="text-[#BDBDBD] text-sm mb-3">
                            Contact our support team:
                          </p>
                          <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                              <span className="text-[#4CAF50]">💬</span>
                              <span className="text-sm text-[#424242]">WhatsApp: Send "help" to our bot</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-[#2196F3]">📧</span>
                              <span className="text-sm text-[#424242]">Email: support@aliran-tunai.com</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HelpModal