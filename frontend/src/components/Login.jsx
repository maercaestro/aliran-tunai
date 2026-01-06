import { useState } from 'react'
import { buildApiUrl, API_ENDPOINTS } from '../config/api'
import brandConfig from '../config/brand'

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
      const response = await fetch(buildApiUrl(API_ENDPOINTS.SEND_OTP), {
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
      console.log('Sending OTP verification request...', { phoneNumber, otp })
      
      const response = await fetch(buildApiUrl(API_ENDPOINTS.VERIFY_OTP), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          phone_number: phoneNumber,
          otp: otp 
        }),
      })

      console.log('Response status:', response.status)
      console.log('Response headers:', response.headers)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        setError(errorData.error || `Server error: ${response.status}`)
        return
      }

      const data = await response.json()
      console.log('Response data:', data)

      if (data.token && data.user) {
        // Store token and user info
        localStorage.setItem('auth_token', data.token)
        localStorage.setItem('user_phone', phoneNumber)
        localStorage.setItem('user_info', JSON.stringify(data.user))
        
        console.log('Login successful, calling onLoginSuccess')
        // Call success callback
        onLoginSuccess(data.user, data.token)
      } else {
        console.error('Invalid response format:', data)
        setError('Invalid response from server')
      }
    } catch (err) {
      console.error('Login error:', err)
      setError(`Connection error: ${err.message}`)
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
    <div className="w-full min-h-screen flex items-center justify-center bg-[#0A192F] relative overflow-hidden">
      {/* Background Ambient Glow */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-[#00F0B5]/10 blur-[120px]"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[#2196F3]/10 blur-[120px]"></div>
      <div className="absolute top-1/2 left-1/6 transform -translate-y-1/2 opacity-[0.05] z-0">
        <img src="/logoaliran-new2.png" alt="" className="w-[600px] h-auto object-contain" />
      </div>

      <div className="relative z-10 w-full max-w-md mx-4">
        <div className="bg-[#10213C]/60 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
          {/* Logo and Title */}
          <div className="flex flex-col items-center mb-8">
            <img src={brandConfig.logo.path} alt={brandConfig.logo.alt} className="h-20 w-auto mb-4 drop-shadow-[0_0_15px_rgba(0,240,181,0.4)]" />
          </div>

          {error && (
            <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-red-400 text-sm text-center">{error}</p>
            </div>
          )}

          {!otpSent ? (
            // Phone Number Input
            <div className="space-y-6">
              <div className="text-left">
                <label className="block text-sm font-medium text-[#B0B8C3] mb-2">
                  Phone Number
                </label>
                <div className="relative group">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[#B0B8C3] text-sm group-focus-within:text-[#00F0B5] transition-colors">
                    +
                  </span>
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={handlePhoneChange}
                    placeholder="60123456789"
                    className="w-full pl-8 pr-4 py-3 bg-[#0A192F]/50 border border-white/10 rounded-xl text-white placeholder-[#B0B8C3]/50 focus:border-[#00F0B5] focus:ring-1 focus:ring-[#00F0B5] outline-none transition-all"
                    disabled={loading}
                  />
                </div>
                <p className="text-xs text-[#B0B8C3]/70 mt-2">
                  Enter your registered WhatsApp number
                </p>
              </div>

              <button
                onClick={sendOTP}
                disabled={loading || !phoneNumber}
                className="w-full py-3 bg-gradient-to-r from-[#00F0B5] to-[#00F0B5]/80 text-[#0A192F] font-bold rounded-xl hover:shadow-[0_0_20px_rgba(0,240,181,0.3)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Sending...' : 'Send Access Code'}
              </button>
            </div>
          ) : (
            // OTP Input
            <div className="space-y-6">
              <div className="text-left">
                <label className="block text-sm font-medium text-[#B0B8C3] mb-2">
                  Verification Code
                </label>
                <input
                  type="text"
                  maxLength="6"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  placeholder="123456"
                  className="w-full px-4 py-3 bg-[#0A192F]/50 border border-white/10 rounded-xl text-white text-center text-2xl tracking-[0.5em] placeholder-[#B0B8C3]/30 focus:border-[#00F0B5] focus:ring-1 focus:ring-[#00F0B5] outline-none transition-all"
                  disabled={loading}
                />
                <p className="text-xs text-[#B0B8C3]/70 mt-2 text-center">
                  Enter the 6-digit code sent to +{phoneNumber}
                </p>
              </div>

              <button
                onClick={verifyOTP}
                disabled={loading || otp.length !== 6}
                className="w-full py-3 bg-gradient-to-r from-[#00F0B5] to-[#00F0B5]/80 text-[#0A192F] font-bold rounded-xl hover:shadow-[0_0_20px_rgba(0,240,181,0.3)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Verifying...' : 'Verify & Sign In'}
              </button>

              <div className="flex justify-between text-sm px-2">
                <button
                  onClick={resendOTP}
                  disabled={loading}
                  className="text-[#00F0B5] hover:text-[#00F0B5]/80 hover:underline disabled:opacity-50 transition-colors"
                >
                  Resend Code
                </button>
                <button
                  onClick={() => {
                    setOtpSent(false)
                    setOtp('')
                    setError('')
                  }}
                  disabled={loading}
                  className="text-[#B0B8C3] hover:text-white hover:underline disabled:opacity-50 transition-colors"
                >
                  Change Number
                </button>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-white/5 text-center">
            <p className="text-xs text-[#B0B8C3]/50">
              Protected by End-to-End Encryption
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login