import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function ModeSelector({ onModeSelect, selectedMode }) {
  const [mode, setMode] = useState(selectedMode)
  const navigate = useNavigate()

  const handleModeSelection = (selectedMode) => {
    setMode(selectedMode)
    onModeSelect(selectedMode)
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            💰 Aliran Tunai
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Choose your financial tracking experience
          </p>
        </div>

        {/* Mode Selection Cards */}
        <div className="grid md:grid-cols-2 gap-8">
          
          {/* Personal Budget Mode */}
          <div 
            className={`relative overflow-hidden rounded-2xl cursor-pointer transition-all duration-300 transform hover:scale-105 ${
              mode === 'personal' 
                ? 'ring-4 ring-indigo-500 shadow-2xl' 
                : 'shadow-lg hover:shadow-xl'
            }`}
            onClick={() => handleModeSelection('personal')}
          >
            <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-8 text-white">
              <div className="flex items-center mb-4">
                <div className="text-4xl mr-4">👤</div>
                <div>
                  <h2 className="text-2xl font-bold">Personal Budget</h2>
                  <p className="text-indigo-200">Track your personal finances</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-6">
              <div className="space-y-3">
                <div className="flex items-center text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  Personal expense tracking
                </div>
                <div className="flex items-center text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  Monthly budget management
                </div>
                <div className="flex items-center text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  Savings goals & targets
                </div>
                <div className="flex items-center text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  Spending insights & alerts
                </div>
                <div className="flex items-center text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  WhatsApp integration
                </div>
              </div>
              
              <div className="mt-6">
                <button className="w-full bg-indigo-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-indigo-700 transition-colors">
                  Start Personal Tracking
                </button>
              </div>
            </div>
          </div>

          {/* Business Mode */}
          <div 
            className={`relative overflow-hidden rounded-2xl cursor-pointer transition-all duration-300 transform hover:scale-105 ${
              mode === 'business' 
                ? 'ring-4 ring-emerald-500 shadow-2xl' 
                : 'shadow-lg hover:shadow-xl'
            }`}
            onClick={() => handleModeSelection('business')}
          >
            <div className="bg-gradient-to-br from-emerald-500 to-teal-600 p-8 text-white">
              <div className="flex items-center mb-4">
                <div className="text-4xl mr-4">🏢</div>
                <div>
                  <h2 className="text-2xl font-bold">Business Finance</h2>
                  <p className="text-emerald-200">Manage business cash flow</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-6">
              <div className="space-y-3">
                <div className="flex items-center text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  Cash Conversion Cycle (CCC)
                </div>
                <div className="flex items-center text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  B2B transaction tracking
                </div>
                <div className="flex items-center text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  Financial health reports
                </div>
                <div className="flex items-center text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  Business categorization
                </div>
                <div className="flex items-center text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  Excel export & analytics
                </div>
              </div>
              
              <div className="mt-6">
                <button className="w-full bg-emerald-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-emerald-700 transition-colors">
                  Start Business Tracking
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