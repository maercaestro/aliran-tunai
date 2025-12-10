import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle, TrendingUp, FileText, Wallet } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 relative overflow-hidden">
      {/* Background Glow Effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16 relative z-10">
        <div className="text-center max-w-4xl mx-auto">
          <img 
            src="/final-logo.png" 
            alt="AliranTunai ERP" 
            className="w-64 h-64 mx-auto mb-8 object-contain drop-shadow-[0_0_30px_rgba(45,212,191,0.4)]"
          />
          <h1 className="text-6xl font-bold text-white mb-6 tracking-tight">
            AliranTunai ERP
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
            Get Started <ArrowRight className="w-5 h-5" />
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
                <h3 className="text-xl font-semibold mb-3 text-teal-400">The Contractor</h3>
                <p className="text-slate-300">
                  En Azlan is a hardworking contractor who takes on heavy construction projects for schools and government buildings. He's built his reputation on quality work and reliability.
                </p>
              </div>
              
              <div className="bg-rose-500/10 p-6 rounded-lg border-l-4 border-rose-500">
                <h3 className="text-xl font-semibold mb-3 text-rose-400">The Problem</h3>
                <p className="text-slate-300 mb-3">
                  Every Thursday, the same nightmare: his workers need their wages by Friday, or they'll have to leave. He scrambles through stacks of receipts, looking for payments that haven't come through yet.
                </p>
                <p className="text-slate-300 mb-3">
                  He rushes to the school to request expedited payment. But the school administration scolds him—his receipts don't have enough information. They need proper invoices with complete details.
                </p>
                <p className="text-slate-300">
                  Usually, he'd hire an accountant to create proper invoices. But this time, it's too late. He has to let his workers go and cancel upcoming projects just to save enough cash to survive until payment arrives.
                </p>
              </div>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 p-8 rounded-lg">
              <div className="text-center">
                <div className="w-32 h-32 mx-auto mb-4 bg-slate-700 rounded-full flex items-center justify-center">
                  <span className="text-5xl">👷</span>
                </div>
                <h4 className="text-2xl font-bold mb-2 text-white">En Azlan</h4>
                <p className="text-slate-400 italic">"I just want to pay my workers on time..."</p>
              </div>
              
              <div className="mt-8 space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-rose-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-xs">✕</span>
                  </div>
                  <p className="text-slate-300">Workers leaving by Friday</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-rose-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-xs">✕</span>
                  </div>
                  <p className="text-slate-300">Receipts rejected by schools</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-rose-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-xs">✕</span>
                  </div>
                  <p className="text-slate-300">No time for accountant</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-rose-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-xs">✕</span>
                  </div>
                  <p className="text-slate-300">Projects cancelled</p>
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
            Introducing AliranTunai ERP
          </h2>
          <p className="text-xl text-center mb-16 text-teal-100">
            Your receipts, transformed into government-compliant e-invoices in seconds
          </p>

          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 p-6 rounded-lg hover:border-teal-500/50 transition-all duration-200">
              <div className="w-14 h-14 bg-teal-500/20 rounded-lg flex items-center justify-center mb-4">
                <FileText className="w-7 h-7 text-teal-400" />
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
                <Wallet className="w-6 h-6 text-teal-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1 text-white">Pay Workers On Time</h4>
                  <p className="text-slate-400 text-sm">Get your payments expedited with proper documentation. Keep your team happy and working.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle className="w-6 h-6 text-teal-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1 text-white">Government-Compliant</h4>
                  <p className="text-slate-400 text-sm">E-invoices meet all LHDN requirements. Schools and agencies accept them immediately.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <TrendingUp className="w-6 h-6 text-teal-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1 text-white">Instant Processing</h4>
                  <p className="text-slate-400 text-sm">From receipt to e-invoice in under 60 seconds. No more waiting for accountants.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <FileText className="w-6 h-6 text-teal-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1 text-white">Always Accessible</h4>
                  <p className="text-slate-400 text-sm">View all your claims and e-invoices anytime from your dashboard. Never lose a receipt again.</p>
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
            Stop Losing Workers. Start Using AliranTunai.
          </h2>
          <p className="text-xl text-slate-300 mb-8">
            Join contractors who are getting paid faster and keeping their projects running smoothly.
          </p>
          <Link 
            to="/login"
            className="inline-flex items-center gap-2 bg-teal-500 text-slate-950 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-teal-400 transition-all duration-200 shadow-lg shadow-teal-500/25"
          >
            Start Free Today <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
