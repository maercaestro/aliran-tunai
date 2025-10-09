import { useState } from 'react'

function Login({ onLoginSuccess }) {
  const [phoneNumber, setPhoneNumber] = useState('')
  const [otp, setOtp] = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Format phone number as user types
  const formatPhoneNumber = (value) => {
    // Remove all non-digits
    const digits = value.replace(/\D/g, '')
    
    // If it starts with 60, keep it
    if (digits.startsWith('60')) {
      return digits
    }
    
    // If it starts with 0, replace with 60
    if (digits.startsWith('0')) {
      return '60' + digits.substring(1)
    }
    
    // If it doesn't start with 60 or 0, add 60
    if (digits.length > 0 && !digits.startsWith('60')) {
      return '60' + digits
    }
    
    return digits
  }

  const handlePhoneChange = (e) => {
    const formatted = formatPhoneNumber(e.target.value)
    // Limit to reasonable phone number length (60 + 9 digits = 11 total)
    if (formatted.length <= 11) {
      setPhoneNumber(formatted)
    }
  }

  const sendOTP = async () => {
    if (!phoneNumber || phoneNumber.length < 10) {
      setError('Please enter a valid Malaysian phone number')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await fetch('/api/auth/send-otp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone_number: phoneNumber }),
      })

      const data = await response.json()

      if (response.ok) {
        setOtpSent(true)
        setError('')
      } else {
        setError(data.error || 'Failed to send OTP')
      }
    } catch (err) {
      setError('Connection error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const verifyOTP = async () => {
    if (!otp || otp.length !== 6) {
      setError('Please enter the 6-digit OTP')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await fetch('/api/auth/verify-otp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          phone_number: phoneNumber,
          otp: otp 
        }),
      })

      const data = await response.json()

      if (response.ok) {
        // Store token and user info
        localStorage.setItem('auth_token', data.token)
        localStorage.setItem('user_phone', phoneNumber)
        localStorage.setItem('user_info', JSON.stringify(data.user))
        
        // Call success callback
        onLoginSuccess(data.user, data.token)
      } else {
        setError(data.error || 'Invalid OTP')
      }
    } catch (err) {
      setError('Connection error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const resendOTP = () => {
    setOtp('')
    setOtpSent(false)
    sendOTP()
  }

  return (
    <div className="w-full min-h-screen flex items-center justify-center" style={{
      background: 'linear-gradient(135deg, #F5F5F5 0%, #F8F9FA 20%, #F5F5F5 40%, rgba(76, 175, 80, 0.02) 60%, #F5F5F5 80%, rgba(255, 179, 0, 0.01) 100%)',
      backgroundSize: '400% 400%',
      animation: 'subtleShift 20s ease-in-out infinite'
    }}>
      {/* Background Logo Watermark */}
      <div className="fixed inset-0 flex items-center justify-center pointer-events-none z-0">
        <img 
          src="/logoaliran.png" 
          alt="Background Logo" 
          className="w-120 h-120 opacity-20"
          style={{
            filter: 'blur(2px)',
            transform: 'rotate(-15deg)'
          }}
        />
      </div>

      <div className="relative z-10 w-full max-w-md mx-4">
        <div className="neuro-card p-8 text-center">
          {/* Logo and Title */}
          <div className="flex flex-col items-center mb-8">
            <img src="/logoaliran.png" alt="AliranTunai Logo" className="h-24 w-24 rounded-lg mb-4" />
            <h1 className="text-2xl font-bold text-[#424242] mb-2">AliranTunai</h1>
            <p className="text-[#BDBDBD] text-sm">Sign in to access your cash flow dashboard</p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {!otpSent ? (
            // Phone Number Input
            <div className="space-y-4">
              <div className="text-left">
                <label className="block text-sm font-medium text-[#424242] mb-2">
                  Phone Number
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[#BDBDBD] text-sm">
                    +
                  </span>
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={handlePhoneChange}
                    placeholder="60123456789"
                    className="neuro-card-inset w-full pl-8 pr-4 py-3 text-[#424242] placeholder-[#BDBDBD] border-none outline-none"
                    style={{background: '#F5F5F5'}}
                    disabled={loading}
                  />
                </div>
                <p className="text-xs text-[#BDBDBD] mt-1">
                  Enter your Malaysian phone number (e.g., 60123456789)
                </p>
              </div>

              <button
                onClick={sendOTP}
                disabled={loading || !phoneNumber}
                className="neuro-button w-full py-3 text-[#424242] font-medium disabled:opacity-50"
              >
                {loading ? 'Sending...' : 'Send OTP'}
              </button>
            </div>
          ) : (
            // OTP Input
            <div className="space-y-4">
              <div className="text-left">
                <label className="block text-sm font-medium text-[#424242] mb-2">
                  Verification Code
                </label>
                <input
                  type="text"
                  maxLength="6"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  placeholder="123456"
                  className="neuro-card-inset w-full px-4 py-3 text-[#424242] text-center text-2xl tracking-widest placeholder-[#BDBDBD] border-none outline-none"
                  style={{background: '#F5F5F5'}}
                  disabled={loading}
                />
                <p className="text-xs text-[#BDBDBD] mt-1">
                  Enter the 6-digit code sent to +{phoneNumber}
                </p>
              </div>

              <button
                onClick={verifyOTP}
                disabled={loading || otp.length !== 6}
                className="neuro-button w-full py-3 text-[#424242] font-medium disabled:opacity-50"
              >
                {loading ? 'Verifying...' : 'Verify & Sign In'}
              </button>

              <div className="flex justify-between text-sm">
                <button
                  onClick={resendOTP}
                  disabled={loading}
                  className="text-[#4CAF50] hover:underline disabled:opacity-50"
                >
                  Resend OTP
                </button>
                <button
                  onClick={() => {
                    setOtpSent(false)
                    setOtp('')
                    setError('')
                  }}
                  disabled={loading}
                  className="text-[#BDBDBD] hover:underline disabled:opacity-50"
                >
                  Change Number
                </button>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="mt-8 pt-4 border-t border-[#BDBDBD]/20">
            <p className="text-xs text-[#BDBDBD]">
              Only registered WhatsApp users can access the dashboard
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login