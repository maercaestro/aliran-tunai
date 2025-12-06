import { useState } from 'react'

function HelpModal({ isOpen, onClose }) {
  const [activeSection, setActiveSection] = useState('getting-started')

  const helpSections = [
    { id: 'getting-started', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg> Getting Started', icon: '<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>' },
    { id: 'whatsapp', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg> WhatsApp Bot', icon: '<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>' },
    { id: 'dashboard', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg> Dashboard', icon: '<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>' },
    { id: 'faq', label: '<svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> FAQ', icon: '<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>' }
  ]

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-[#10213C] border border-white/10 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-[#00F0B5] to-[#2196F3] rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(0,240,181,0.3)]">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-white">Help & Support</h2>
            </div>
            <button
              onClick={onClose}
              className="text-[#B0B8C3] hover:text-white text-xl font-bold transition-colors"
            >
              ×
            </button>
          </div>

          <div className="flex flex-col lg:flex-row gap-6">
            {/* Sidebar */}
            <div className="lg:w-1/4">
              <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-3 space-y-2">
                {helpSections.map(section => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full text-left p-3 rounded-lg transition-all ${
                      activeSection === section.id 
                        ? 'bg-[#00F0B5] text-[#0A192F] font-medium' 
                        : 'text-[#B0B8C3] hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <span className="lg:hidden" dangerouslySetInnerHTML={{ __html: section.icon }}></span>
                    <span className="hidden lg:inline" dangerouslySetInnerHTML={{ __html: section.label }}></span>
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
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-[#00F0B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        Getting Started with Aliran
                      </h3>
                      
                      <div className="space-y-4">
                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-2">1. WhatsApp Registration</h4>
                          <p className="text-[#B0B8C3] text-sm">
                            First, you need to register via WhatsApp by providing your business information:
                          </p>
                          <ul className="list-disc list-inside text-[#B0B8C3] text-sm mt-2 ml-4">
                            <li>Owner name</li>
                            <li>Company name</li>
                            <li>Location</li>
                            <li>Business type</li>
                          </ul>
                        </div>

                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-2">2. Dashboard Login</h4>
                          <p className="text-[#B0B8C3] text-sm">
                            After registration, you can access this dashboard using your phone number and OTP verification.
                          </p>
                        </div>

                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-2">3. Start Tracking</h4>
                          <p className="text-[#B0B8C3] text-sm">
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
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-[#00F0B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                        WhatsApp Bot Guide
                      </h3>
                      
                      <div className="space-y-4">
                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-3">How to Record Transactions</h4>
                          <p className="text-[#B0B8C3] text-sm mb-3">
                            Simply send a message describing your transaction in natural language:
                          </p>
                          
                          <div className="space-y-3">
                            <div className="bg-[#00F0B5]/10 border border-[#00F0B5]/20 p-3 rounded-lg">
                              <p className="text-sm font-mono text-[#00F0B5]">
                                "Sold 5 pieces of clothing for RM 50 each"
                              </p>
                              <p className="text-xs text-[#00F0B5]/70 mt-1">→ Records RM 250 sale</p>
                            </div>
                            
                            <div className="bg-[#2196F3]/10 border border-[#2196F3]/20 p-3 rounded-lg">
                              <p className="text-sm font-mono text-[#2196F3]">
                                "Bought inventory from supplier for RM 800"
                              </p>
                              <p className="text-xs text-[#2196F3]/70 mt-1">→ Records RM 800 purchase</p>
                            </div>
                            
                            <div className="bg-orange-500/10 border border-orange-500/20 p-3 rounded-lg">
                              <p className="text-sm font-mono text-orange-400">
                                "Received payment RM 300 from customer Ali"
                              </p>
                              <p className="text-xs text-orange-400/70 mt-1">→ Records RM 300 payment received</p>
                            </div>
                          </div>
                        </div>

                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-3">Supported Transaction Types</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div className="flex items-center space-x-2">
                              <svg className="w-4 h-4 text-[#00F0B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                              </svg>
                              <span className="text-sm text-white">Sales</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <svg className="w-4 h-4 text-[#2196F3]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                              </svg>
                              <span className="text-sm text-white">Purchases</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                              </svg>
                              <span className="text-sm text-white">Expenses</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <svg className="w-4 h-4 text-[#00F0B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                              </svg>
                              <span className="text-sm text-white">Payments Received</span>
                            </div>
                          </div>
                        </div>

                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-3">Tips for Better Recognition</h4>
                          <ul className="space-y-2 text-sm text-[#B0B8C3]">
                            <li className="flex items-start space-x-2">
                              <svg className="w-4 h-4 text-[#00F0B5] mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              <span>Include amounts in RM (Malaysian Ringgit)</span>
                            </li>
                            <li className="flex items-start space-x-2">
                              <svg className="w-4 h-4 text-[#00F0B5] mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              <span>Use clear action words like "sold", "bought", "received", "paid"</span>
                            </li>
                            <li className="flex items-start space-x-2">
                              <svg className="w-4 h-4 text-[#00F0B5] mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              <span>Mention quantities when applicable</span>
                            </li>
                            <li className="flex items-start space-x-2">
                              <svg className="w-4 h-4 text-[#00F0B5] mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
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
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-[#00F0B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                        Dashboard Features
                      </h3>
                      
                      <div className="space-y-4">
                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-3">Cash Conversion Cycle (CCC)</h4>
                          <p className="text-[#B0B8C3] text-sm mb-3">
                            The main metric showing how efficiently your business converts investments into cash flows.
                          </p>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                            <div className="text-center">
                              <div className="text-[#00F0B5] font-semibold">&lt; 30 days</div>
                              <div className="text-[#B0B8C3]">Excellent</div>
                            </div>
                            <div className="text-center">
                              <div className="text-[#2196F3] font-semibold">30-60 days</div>
                              <div className="text-[#B0B8C3]">Good</div>
                            </div>
                            <div className="text-center">
                              <div className="text-orange-400 font-semibold">60-90 days</div>
                              <div className="text-[#B0B8C3]">Moderate</div>
                            </div>
                            <div className="text-center">
                              <div className="text-red-400 font-semibold">&gt; 90 days</div>
                              <div className="text-[#B0B8C3]">Needs Attention</div>
                            </div>
                          </div>
                        </div>

                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-3">Financial Summary</h4>
                          <p className="text-[#B0B8C3] text-sm">
                            View your total sales, purchases, and cash flow at a glance. The summary updates automatically as you add new transactions.
                          </p>
                        </div>

                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-3">Recent Transactions</h4>
                          <p className="text-[#B0B8C3] text-sm">
                            See your latest business activities with details like amount, type, and date. Click the Excel button to download your complete transaction history.
                          </p>
                        </div>

                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-3">Quick Actions</h4>
                          <p className="text-[#B0B8C3] text-sm mb-3">
                            Use the buttons at the bottom to:
                          </p>
                          <ul className="space-y-1 text-sm text-[#B0B8C3] ml-4">
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
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-[#00F0B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Frequently Asked Questions
                      </h3>
                      
                      <div className="space-y-4">
                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-2">How do I register for Aliran?</h4>
                          <p className="text-[#B0B8C3] text-sm">
                            Send a message to our WhatsApp bot. You'll be guided through a 4-step registration process where you provide your owner name, company name, location, and business type.
                          </p>
                        </div>

                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-2">Is my data secure?</h4>
                          <p className="text-[#B0B8C3] text-sm">
                            Yes! Your data is stored securely in our encrypted database. Each user can only access their own data, and we use industry-standard security practices.
                          </p>
                        </div>

                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-2">Can I edit or delete transactions?</h4>
                          <p className="text-[#B0B8C3] text-sm">
                            Currently, transactions are recorded as permanent entries for audit purposes. If you made an error, you can add a correcting transaction or contact support.
                          </p>
                        </div>

                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-2">What happens if I lose access to my WhatsApp?</h4>
                          <p className="text-[#B0B8C3] text-sm">
                            Your data is tied to your phone number. If you change numbers, contact our support team to transfer your account.
                          </p>
                        </div>

                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-2">How can I export my data?</h4>
                          <p className="text-[#B0B8C3] text-sm">
                            Use the Excel export button in the dashboard header or go to Settings → Data → Export Data to download your complete transaction history.
                          </p>
                        </div>

                        <div className="bg-[#0A192F]/50 border border-white/10 rounded-xl p-4">
                          <h4 className="font-semibold text-white mb-2">Need more help?</h4>
                          <p className="text-[#B0B8C3] text-sm mb-3">
                            Contact our support team:
                          </p>
                          <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                              <svg className="w-4 h-4 text-[#00F0B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                              </svg>
                              <span className="text-sm text-white">WhatsApp: Send "help" to our bot</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <svg className="w-4 h-4 text-[#2196F3]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                              </svg>
                              <span className="text-sm text-white">Email: support@aliran-tunai.com</span>
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