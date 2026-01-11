import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { sendOTP, verifyOTP } from '../api/workOrders';

export default function Login() {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState('phone'); // 'phone' or 'otp'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSendOTP = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await sendOTP(phoneNumber);
      setStep('otp');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await verifyOTP(phoneNumber, otp);
      
      // Mark that user has visited before
      localStorage.setItem('visited_before', 'true');
      
      login(response.user, response.token);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Glow Effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-2xl shadow-2xl p-8 w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <img src="/final-logo.png" alt="AliranTunai ERP" className="h-24 mx-auto mb-6 object-contain drop-shadow-[0_0_15px_rgba(45,212,191,0.3)]" />
          <h1 className="text-2xl font-bold text-white mb-2 tracking-tight">AliranTunai ERP</h1>
          <p className="text-slate-400 font-medium">Enterprise Contractor Management</p>
        </div>        {step === 'phone' ? (
          <form onSubmit={handleSendOTP} className="space-y-6">
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                Phone Number
              </label>
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="60123456789"
                className="w-full px-4 py-3 bg-slate-950/50 border border-slate-700 rounded-lg focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 text-slate-200 placeholder-slate-600 transition-all duration-200 font-mono"
                required
              />
              <p className="mt-2 text-xs text-slate-500">Enter your WhatsApp number with country code</p>
            </div>

            {error && (
              <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_20px_rgba(45,212,191,0.2)] hover:shadow-[0_0_30px_rgba(45,212,191,0.4)]"
            >
              {loading ? 'INITIATING...' : 'SEND ACCESS CODE'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOTP} className="space-y-6">
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                Security Code
              </label>
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="123456"
                maxLength="6"
                className="w-full px-4 py-3 bg-slate-950/50 border border-slate-700 rounded-lg focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 text-slate-200 placeholder-slate-600 text-center text-2xl tracking-[0.5em] font-mono transition-all duration-200"
                required
              />
              <p className="mt-2 text-xs text-slate-500 text-center">Check your WhatsApp for the code</p>
            </div>

            {error && (
              <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_20px_rgba(45,212,191,0.2)] hover:shadow-[0_0_30px_rgba(45,212,191,0.4)]"
            >
              {loading ? 'VERIFYING...' : 'AUTHENTICATE'}
            </button>

            <button
              type="button"
              onClick={() => {
                setStep('phone');
                setOtp('');
                setError('');
              }}
              className="w-full text-slate-400 hover:text-teal-400 text-sm transition-colors duration-200"
            >
              ← Return to phone entry
            </button>
          </form>
        )}

        <div className="mt-8 pt-6 border-t border-slate-800 text-center text-xs text-slate-600">
          <p>System Access Restricted. Authorized Personnel Only.</p>
        </div>
      </div>
    </div>
  );
}
