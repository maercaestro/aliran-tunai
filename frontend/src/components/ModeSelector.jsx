import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function ModeSelector({ onModeSelect, selectedMode, isAuthenticated, user }) {
  const [mode, setMode] = useState(selectedMode)
  const navigate = useNavigate()

  const handleModeSelection = (selectedMode) => {
    setMode(selectedMode)
    onModeSelect(selectedMode)
    
    // If user is authenticated, go to dashboard, otherwise go to login
    if (isAuthenticated) {
      navigate(`/${selectedMode}/dashboard`)
    } else {
      navigate('/login')
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        {/* Header */}
        <div className="text-center mb-12">
          {/* Neuromorphic logo container */}
          <div className="inline-flex items-center justify-center w-24 h-24 mb-6 bg-gray-100 rounded-2xl shadow-[8px_8px_16px_#b8b8b8,-8px_-8px_16px_#ffffff] border border-gray-200 p-2">
            <img 
              src="/logoaliran.png" 
              alt="Aliran Tunai Logo" 
              className="w-full h-full object-contain"
            />
          </div>
          <h1 className="text-5xl font-bold text-gray-800 mb-4 drop-shadow-sm">
            Aliran Tunai
          </h1>
          {isAuthenticated && user ? (
            <div className="mb-8">
              <p className="text-xl text-gray-600 mb-2">
                Welcome back, {user.owner_name || user.email}!
              </p>
              <p className="text-lg text-gray-500">
                Choose your financial tracking mode
              </p>
            </div>
          ) : (
            <p className="text-xl text-gray-600 mb-8">
              Choose your financial tracking experience
            </p>
          )}
        </div>

        {/* Mode Selection Cards */}
        <div className="grid md:grid-cols-2 gap-8">
          
          {/* Personal Budget Mode */}
          <div 
            className={`relative cursor-pointer transition-all duration-300 ${
              mode === 'personal' 
                ? 'bg-gray-50 shadow-[inset_8px_8px_16px_#b8b8b8,inset_-8px_-8px_16px_#ffffff] border-2 border-indigo-200' 
                : 'bg-gray-100 shadow-[8px_8px_16px_#b8b8b8,-8px_-8px_16px_#ffffff] hover:shadow-[12px_12px_24px_#a8a8a8,-12px_-12px_24px_#ffffff]'
            } rounded-3xl border border-gray-200 p-1`}
            onClick={() => handleModeSelection('personal')}
          >
            <div className="bg-gray-100 rounded-3xl p-8 shadow-[inset_4px_4px_8px_#d1d1d1,inset_-4px_-4px_8px_#ffffff]">
              {/* Icon container */}
              <div className="flex items-center mb-6">
                <div className="flex items-center justify-center w-16 h-16 mr-4 bg-gray-100 rounded-2xl shadow-[6px_6px_12px_#b8b8b8,-6px_-6px_12px_#ffffff] border border-gray-200">
                  <span className="text-2xl">👤</span>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-800">Personal Budget</h2>
                  <p className="text-gray-600">Track your personal finances</p>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-b-3xl p-6 border-t border-gray-200">
              <div className="space-y-3">
                <div className="flex items-center text-gray-700">
                  <div className="flex items-center justify-center w-6 h-6 mr-3 bg-gray-100 rounded-lg shadow-[3px_3px_6px_#b8b8b8,-3px_-3px_6px_#ffffff] border border-gray-200">
                    <span className="text-green-600 text-sm font-bold">✓</span>
                  </div>
                  Personal expense tracking
                </div>
                <div className="flex items-center text-gray-700">
                  <div className="flex items-center justify-center w-6 h-6 mr-3 bg-gray-100 rounded-lg shadow-[3px_3px_6px_#b8b8b8,-3px_-3px_6px_#ffffff] border border-gray-200">
                    <span className="text-green-600 text-sm font-bold">✓</span>
                  </div>
                  Monthly budget management
                </div>
                <div className="flex items-center text-gray-700">
                  <div className="flex items-center justify-center w-6 h-6 mr-3 bg-gray-100 rounded-lg shadow-[3px_3px_6px_#b8b8b8,-3px_-3px_6px_#ffffff] border border-gray-200">
                    <span className="text-green-600 text-sm font-bold">✓</span>
                  </div>
                  Savings goals & targets
                </div>
                <div className="flex items-center text-gray-700">
                  <div className="flex items-center justify-center w-6 h-6 mr-3 bg-gray-100 rounded-lg shadow-[3px_3px_6px_#b8b8b8,-3px_-3px_6px_#ffffff] border border-gray-200">
                    <span className="text-green-600 text-sm font-bold">✓</span>
                  </div>
                  Spending insights & alerts
                </div>
                <div className="flex items-center text-gray-700">
                  <div className="flex items-center justify-center w-6 h-6 mr-3 bg-gray-100 rounded-lg shadow-[3px_3px_6px_#b8b8b8,-3px_-3px_6px_#ffffff] border border-gray-200">
                    <span className="text-green-600 text-sm font-bold">✓</span>
                  </div>
                  WhatsApp integration
                </div>
              </div>
              
              <div className="mt-6">
                <button className="w-full bg-gray-100 text-gray-800 py-4 px-6 rounded-2xl font-semibold transition-all duration-200 shadow-[8px_8px_16px_#b8b8b8,-8px_-8px_16px_#ffffff] border border-gray-200 hover:shadow-[inset_8px_8px_16px_#b8b8b8,inset_-8px_-8px_16px_#ffffff] active:shadow-[inset_8px_8px_16px_#b8b8b8,inset_-8px_-8px_16px_#ffffff]">
                  {isAuthenticated ? 'Go to Personal Dashboard' : 'Start Personal Tracking'}
                </button>
              </div>
            </div>
          </div>

          {/* Business Mode */}
          <div 
            className={`relative cursor-pointer transition-all duration-300 ${
              mode === 'business' 
                ? 'bg-gray-50 shadow-[inset_8px_8px_16px_#b8b8b8,inset_-8px_-8px_16px_#ffffff] border-2 border-emerald-200' 
                : 'bg-gray-100 shadow-[8px_8px_16px_#b8b8b8,-8px_-8px_16px_#ffffff] hover:shadow-[12px_12px_24px_#a8a8a8,-12px_-12px_24px_#ffffff]'
            } rounded-3xl border border-gray-200 p-1`}
            onClick={() => handleModeSelection('business')}
          >
            <div className="bg-gray-100 rounded-3xl p-8 shadow-[inset_4px_4px_8px_#d1d1d1,inset_-4px_-4px_8px_#ffffff]">
              {/* Icon container */}
              <div className="flex items-center mb-6">
                <div className="flex items-center justify-center w-16 h-16 mr-4 bg-gray-100 rounded-2xl shadow-[6px_6px_12px_#b8b8b8,-6px_-6px_12px_#ffffff] border border-gray-200">
                  <span className="text-2xl">🏢</span>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-800">Business Finance</h2>
                  <p className="text-gray-600">Manage business cash flow</p>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-b-3xl p-6 border-t border-gray-200">
              <div className="space-y-3">
                <div className="flex items-center text-gray-700">
                  <div className="flex items-center justify-center w-6 h-6 mr-3 bg-gray-100 rounded-lg shadow-[3px_3px_6px_#b8b8b8,-3px_-3px_6px_#ffffff] border border-gray-200">
                    <span className="text-green-600 text-sm font-bold">✓</span>
                  </div>
                  Cash Conversion Cycle (CCC)
                </div>
                <div className="flex items-center text-gray-700">
                  <div className="flex items-center justify-center w-6 h-6 mr-3 bg-gray-100 rounded-lg shadow-[3px_3px_6px_#b8b8b8,-3px_-3px_6px_#ffffff] border border-gray-200">
                    <span className="text-green-600 text-sm font-bold">✓</span>
                  </div>
                  B2B transaction tracking
                </div>
                <div className="flex items-center text-gray-700">
                  <div className="flex items-center justify-center w-6 h-6 mr-3 bg-gray-100 rounded-lg shadow-[3px_3px_6px_#b8b8b8,-3px_-3px_6px_#ffffff] border border-gray-200">
                    <span className="text-green-600 text-sm font-bold">✓</span>
                  </div>
                  Financial health reports
                </div>
                <div className="flex items-center text-gray-700">
                  <div className="flex items-center justify-center w-6 h-6 mr-3 bg-gray-100 rounded-lg shadow-[3px_3px_6px_#b8b8b8,-3px_-3px_6px_#ffffff] border border-gray-200">
                    <span className="text-green-600 text-sm font-bold">✓</span>
                  </div>
                  Business categorization
                </div>
                <div className="flex items-center text-gray-700">
                  <div className="flex items-center justify-center w-6 h-6 mr-3 bg-gray-100 rounded-lg shadow-[3px_3px_6px_#b8b8b8,-3px_-3px_6px_#ffffff] border border-gray-200">
                    <span className="text-green-600 text-sm font-bold">✓</span>
                  </div>
                  Excel export & analytics
                </div>
              </div>
              
              <div className="mt-6">
                <button className="w-full bg-gray-100 text-gray-800 py-4 px-6 rounded-2xl font-semibold transition-all duration-200 shadow-[8px_8px_16px_#b8b8b8,-8px_-8px_16px_#ffffff] border border-gray-200 hover:shadow-[inset_8px_8px_16px_#b8b8b8,inset_-8px_-8px_16px_#ffffff] active:shadow-[inset_8px_8px_16px_#b8b8b8,inset_-8px_-8px_16px_#ffffff]">
                  {isAuthenticated ? 'Go to Business Dashboard' : 'Start Business Tracking'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Additional Info */}
        <div className="text-center mt-12">
          <p className="text-gray-600 mb-4">
            💡 You can switch between modes anytime from your dashboard
          </p>
          <div className="text-sm text-gray-500">
            Powered by AI • WhatsApp Integration • Secure & Private
          </div>
        </div>
      </div>
    </div>
  )
}

export default ModeSelector