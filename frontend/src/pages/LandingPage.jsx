import { Link } from 'react-router-dom';
import { ArrowRightIcon, CheckCircleIcon, TrendingUpIcon, DocumentTextIcon, WalletIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline';
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
            Work flows, cash follows
          </p>
          <p className="text-xl text-slate-300 mb-12">
            Transform your receipts into verified e-invoices instantly. Get paid faster, keep your workers happy.
          </p>
          <Link 
            to="/login"
            className="inline-flex items-center gap-2 bg-teal-500 text-slate-950 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-teal-400 transition-all duration-200 shadow-lg shadow-teal-500/25"
          >
            Get Started <ArrowRightIcon className="w-5 h-5" />
          </Link>
        </div>
      </div>

      {/* Persona Section */}
      <div className="bg-slate-900/50 backdrop-blur-md py-20 relative z-10">
        <div className="container mx-auto px-4 max-w-5xl">
          <h2 className="text-4xl font-bold text-center mb-12 text-white">
            Meet En Azlan
          </h2>
          
          <div className="grid md:grid-cols-2 gap-12 items-center mb-16">
            <div className="space-y-6">
              <div className="bg-teal-500/10 p-6 rounded-lg border-l-4 border-teal-500">
                <h3 className="text-xl font-semibold mb-3 text-teal-400">The "Digital" Contractor</h3>
                <p className="text-slate-300">
                  En Azlan thinks he's digital. He hires a clerk for RM 1,500 a month to key in his receipts from a messy shoebox of fading papers.
                </p>
              </div>
              
              <div className="bg-amber-500/10 p-6 rounded-lg border-l-4 border-amber-500">
                <h3 className="text-xl font-semibold mb-3 text-amber-400">The Zombie Data Trap</h3>
                <p className="text-slate-300 mb-3">
                  But here's the trap: The clerk is just typing from fading receipts. She isn't checking for Tax Compliance. She's creating <span className="font-bold text-amber-300">'Zombie Data'</span>—it looks real, but it's legally worthless.
                </p>
              </div>
              
              <div className="bg-rose-500/10 p-6 rounded-lg border-l-4 border-rose-500">
                <h3 className="text-xl font-semibold mb-3 text-rose-400">The December Panic</h3>
                <p className="text-slate-300">
                  Every December, Azlan panics. He has to hire another expensive accountant just to clean up 12 months of bad data to avoid an LHDN fine.
                </p>
              </div>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 p-8 rounded-lg">
              <div className="text-center">
                <div className="w-32 h-32 mx-auto mb-4 bg-slate-700 rounded-full flex items-center justify-center">
                  <span className="text-5xl">👷</span>
                </div>
                <h4 className="text-2xl font-bold mb-2 text-white">En Azlan</h4>
                <p className="text-slate-400 italic">"I thought I was digital..."</p>
              </div>
              
              <div className="mt-8 space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-rose-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-xs">✕</span>
                  </div>
                  <p className="text-slate-300">RM 1,500/month for clerk</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-rose-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-xs">✕</span>
                  </div>
                  <p className="text-slate-300">Zombie data (not tax compliant)</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-rose-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-xs">✕</span>
                  </div>
                  <p className="text-slate-300">December clean-up fees</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-rose-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-xs">✕</span>
                  </div>
                  <p className="text-slate-300">LHDN fine anxiety</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Solution Section */}
      <div className="bg-gradient-to-b from-teal-500/20 to-teal-600/20 py-20 text-white relative z-10">
        <div className="container mx-auto px-4 max-w-5xl">
          <h2 className="text-4xl font-bold text-center mb-6">
            Aliran Kills the Clean-Up Fee
          </h2>
          <p className="text-xl text-center mb-16 text-teal-100">
            We validate data at the source in January, so December is boring.
          </p>

          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 p-6 rounded-lg hover:border-teal-500/50 transition-all duration-200">
              <div className="w-14 h-14 bg-teal-500/20 rounded-lg flex items-center justify-center mb-4">
                <DocumentTextIcon className="w-7 h-7 text-teal-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Snap Your Receipt</h3>
              <p className="text-slate-300">
                Just take a photo of your receipt and send it via WhatsApp or Telegram. That's it.
              </p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 p-6 rounded-lg hover:border-teal-500/50 transition-all duration-200">
              <div className="w-14 h-14 bg-teal-500/20 rounded-lg flex items-center justify-center mb-4">
                <CheckCircle className="w-7 h-7 text-teal-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">AI Verification</h3>
              <p className="text-slate-300">
                Our AI instantly verifies your receipt stamp and extracts all details—amount, date, project info.
              </p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 p-6 rounded-lg hover:border-teal-500/50 transition-all duration-200">
              <div className="w-14 h-14 bg-teal-500/20 rounded-lg flex items-center justify-center mb-4">
                <TrendingUp className="w-7 h-7 text-teal-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Get Your E-Invoice</h3>
              <p className="text-slate-300">
                Receive a government-compliant e-invoice ready to submit for expedited payment. No accountant needed.
              </p>
            </div>
          </div>

          {/* Benefits */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-700 rounded-lg p-8">
            <h3 className="text-2xl font-bold mb-6 text-center text-white">For Contractors Like En Azlan</h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-6 h-6 text-teal-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1 text-white">No More Zombie Data</h4>
                  <p className="text-slate-400 text-sm">Tax-compliant from Day 1. Every receipt validated instantly, not 12 months later.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <WalletIcon className="w-6 h-6 text-teal-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1 text-white">Kill the Clean-Up Fee</h4>
                  <p className="text-slate-400 text-sm">No more December panic. No expensive accountant to fix bad data. Validate at source, save thousands.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <TrendingUpIcon className="w-6 h-6 text-teal-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1 text-white">LHDN-Ready Always</h4>
                  <p className="text-slate-400 text-sm">Sleep soundly. Every e-invoice meets LHDN requirements. Audit-ready from January to December.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <DocumentTextIcon className="w-6 h-6 text-teal-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1 text-white">Fire Your RM 1,500 Clerk</h4>
                  <p className="text-slate-400 text-sm">AI processes receipts faster and more accurately. No more shoebox. No more fading papers. No more typing errors.</p>
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
            Stop Paying Clean-Up Fees. Start Using Aliran.
          </h2>
          <p className="text-xl text-slate-300 mb-8">
            Validate at the source in January. Make December boring.
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
