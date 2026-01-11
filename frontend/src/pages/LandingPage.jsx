import { Link } from 'react-router-dom';
import { ArrowRightIcon, CheckCircleIcon, ArrowTrendingUpIcon, DocumentTextIcon, WalletIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import brandConfig from '../config/brand';

export default function LandingPage() {
  const { isAuthenticated } = useAuth();
  
  return (
    <div className="min-h-screen bg-slate-950 relative overflow-hidden">
      {/* Navigation Header */}
      <nav className="absolute top-0 left-0 right-0 z-20 bg-slate-900/50 backdrop-blur-md border-b border-slate-800">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <img src={brandConfig.logo.path} alt={brandConfig.logo.alt} className="h-10 object-contain drop-shadow-[0_0_10px_rgba(45,212,191,0.2)]" />
          </div>
          <Link 
            to={isAuthenticated ? "/dashboard" : "/login"}
            className="flex items-center gap-2 px-4 py-2 text-slate-300 hover:text-teal-400 hover:bg-teal-500/10 rounded-lg transition"
          >
            <ArrowRightOnRectangleIcon className="w-4.5 h-4.5" />
            <span>{isAuthenticated ? "Dashboard" : "Login"}</span>
          </Link>
        </div>
      </nav>
      
      {/* Background Glow Effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16 relative z-10 pt-24">{/* Added pt-24 for nav spacing */}
        <div className="text-center max-w-4xl mx-auto">
          <img 
            src={brandConfig.logo.path} 
            alt={brandConfig.logo.alt} 
            className="w-64 h-64 mx-auto mb-8 object-contain drop-shadow-[0_0_30px_rgba(45,212,191,0.4)]"
          />
          <h1 className="text-6xl font-bold text-white mb-6 tracking-tight">
            {brandConfig.name}
          </h1>
          <p className="text-4xl font-medium text-teal-400 mb-8">
            Take Control of Your Cash Flow
          </p>
          <p className="text-xl text-slate-300 mb-12">
            Intelligent financial management powered by AI. Track income and expenses effortlessly through WhatsApp—for your personal finances or business operations.
          </p>
          <Link 
            to="/login"
            onClick={() => localStorage.setItem('visited_before', 'true')}
            className="inline-flex items-center gap-2 bg-teal-500 text-slate-950 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-teal-400 transition-all duration-200 shadow-lg shadow-teal-500/25"
          >
            Get Started <ArrowRightIcon className="w-5 h-5" />
          </Link>
        </div>
      </div>

      {/* Problem/Solution Section */}
      <div className="bg-slate-900/50 backdrop-blur-md py-20 relative z-10">
        <div className="container mx-auto px-4 max-w-5xl">
          <h2 className="text-4xl font-bold text-center mb-12 text-white">
            Financial Clarity Shouldn't Be Hard
          </h2>
          
          <div className="grid md:grid-cols-2 gap-12 items-start mb-16">
            <div className="space-y-6">
              <div className="bg-rose-500/10 p-6 rounded-lg border-l-4 border-rose-500">
                <h3 className="text-xl font-semibold mb-3 text-rose-400">The Old Way</h3>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-start gap-2">
                    <span className="text-rose-400 mt-1">✕</span>
                    <span>Receipts scattered across wallets, drawers, and emails</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-rose-400 mt-1">✕</span>
                    <span>Manual data entry into spreadsheets or accounting software</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-rose-400 mt-1">✕</span>
                    <span>Hours wasted categorizing and reconciling transactions</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-rose-400 mt-1">✕</span>
                    <span>No real-time visibility into your cash position</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-rose-400 mt-1">✕</span>
                    <span>Tax season panic and compliance anxiety</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-teal-500/10 p-6 rounded-lg border-l-4 border-teal-500">
                <h3 className="text-xl font-semibold mb-3 text-teal-400">The {brandConfig.name} Way</h3>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-start gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-teal-400 mt-1 flex-shrink-0" />
                    <span>Just snap a photo via WhatsApp—we handle the rest</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-teal-400 mt-1 flex-shrink-0" />
                    <span>AI extracts and categorizes all transaction details instantly</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-teal-400 mt-1 flex-shrink-0" />
                    <span>Real-time dashboard shows your cash flow at a glance</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-teal-400 mt-1 flex-shrink-0" />
                    <span>Track personal spending or business operations seamlessly</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-teal-400 mt-1 flex-shrink-0" />
                    <span>Tax-compliant records ready when you need them</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="bg-gradient-to-b from-teal-500/20 to-teal-600/20 py-20 text-white relative z-10">
        <div className="container mx-auto px-4 max-w-5xl">
          <h2 className="text-4xl font-bold text-center mb-6">
            How {brandConfig.name} Works
          </h2>
          <p className="text-xl text-center mb-16 text-teal-100">
            Financial management through WhatsApp—it's that simple.
          </p>

          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 p-6 rounded-lg hover:border-teal-500/50 transition-all duration-200">
              <div className="w-14 h-14 bg-teal-500/20 rounded-lg flex items-center justify-center mb-4">
                <DocumentTextIcon className="w-7 h-7 text-teal-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Send via WhatsApp</h3>
              <p className="text-slate-300">
                Snap a photo of your receipt or invoice and send it to our WhatsApp number. No apps to download.
              </p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 p-6 rounded-lg hover:border-teal-500/50 transition-all duration-200">
              <div className="w-14 h-14 bg-teal-500/20 rounded-lg flex items-center justify-center mb-4">
                <CheckCircleIcon className="w-7 h-7 text-teal-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">AI Processing</h3>
              <p className="text-slate-300">
                Our AI extracts all details—amount, date, vendor, category—and automatically categorizes your transaction.
              </p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 p-6 rounded-lg hover:border-teal-500/50 transition-all duration-200">
              <div className="w-14 h-14 bg-teal-500/20 rounded-lg flex items-center justify-center mb-4">
                <ArrowTrendingUpIcon className="w-7 h-7 text-teal-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Track Your Cash Flow</h3>
              <p className="text-slate-300">
                View your updated dashboard instantly. See income, expenses, and cash position in real-time.
              </p>
            </div>
          </div>

          {/* Benefits */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-700 rounded-lg p-8">
            <h3 className="text-2xl font-bold mb-6 text-center text-white">Perfect for Personal & Business</h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="flex items-start gap-3">
                <CheckCircleIcon className="w-6 h-6 text-teal-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1 text-white">Personal Finance Made Simple</h4>
                  <p className="text-slate-400 text-sm">Track daily expenses, monitor your budget, and understand where your money goes—all through WhatsApp.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <WalletIcon className="w-6 h-6 text-teal-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1 text-white">Business Cash Flow Control</h4>
                  <p className="text-slate-400 text-sm">Manage business expenses, track project costs, and maintain tax-compliant records effortlessly.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <ArrowTrendingUpIcon className="w-6 h-6 text-teal-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1 text-white">Real-Time Insights</h4>
                  <p className="text-slate-400 text-sm">Know your cash position at any moment. Make informed decisions with up-to-date financial data.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <DocumentTextIcon className="w-6 h-6 text-teal-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1 text-white">Tax-Ready Records</h4>
                  <p className="text-slate-400 text-sm">Every transaction properly categorized and stored. Tax season becomes a breeze, not a nightmare.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-20 text-center relative z-10">
        <div className="container mx-auto px-4 max-w-3xl">
          <h2 className="text-4xl font-bold mb-6 text-white">
            Take Control of Your Finances Today
          </h2>
          <p className="text-xl text-slate-300 mb-8">
            Join thousands managing their cash flow the smart way.
          </p>
          <Link 
            to="/login"
            className="inline-flex items-center gap-2 bg-teal-500 text-slate-950 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-teal-400 transition-all duration-200 shadow-lg shadow-teal-500/25"
          >
            Start Free Today <ArrowRightIcon className="w-5 h-5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
