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
        // Special handling for WhatsApp 24-hour window error
        if (data.requiresWhatsAppMessage) {
          setError(data.error || 'Please message our WhatsApp Business number first, then try again.')
        } else {
          setError(data.error || 'Failed to send OTP')
        }
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

              {/* WhatsApp Instruction Notice */}
              <div className="p-4 bg-gradient-to-r from-teal-500/10 to-cyan-500/10 border border-teal-500/30 rounded-xl">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-teal-500/20 rounded-lg flex items-center justify-center mt-0.5">
                    <svg className="w-5 h-5 text-teal-400" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-teal-100 font-medium mb-1">Before requesting OTP:</p>
                    <p className="text-xs text-teal-200/80">
                      Send any message to our WhatsApp Business number first to activate the 24-hour messaging window.
                    </p>
                  </div>
                </div>
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