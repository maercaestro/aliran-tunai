import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle, TrendingUp, FileText, Wallet } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <img 
            src="/logoaliran.png" 
            alt="AliranTunai Logo" 
            className="w-48 h-48 mx-auto mb-8 object-contain"
          />
          <h1 className="text-6xl font-bold text-gray-900 mb-6">
            AliranTunai
          </h1>
          <p className="text-3xl font-medium text-blue-600 mb-8">
            Work flows, cash follows
          </p>
          <p className="text-xl text-gray-600 mb-12">
            Transform your receipts into verified e-invoices instantly. Get paid faster, keep your workers happy.
          </p>
          <Link 
            to="/login"
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            Get Started <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>

      {/* Persona Section */}
      <div className="bg-white py-20">
        <div className="container mx-auto px-4 max-w-5xl">
          <h2 className="text-4xl font-bold text-center mb-12 text-gray-900">
            Meet En Azlan
          </h2>
          
          <div className="grid md:grid-cols-2 gap-12 items-center mb-16">
            <div className="space-y-6">
              <div className="bg-blue-50 p-6 rounded-lg border-l-4 border-blue-600">
                <h3 className="text-xl font-semibold mb-3 text-gray-900">The Contractor</h3>
                <p className="text-gray-700">
                  En Azlan is a hardworking contractor who takes on heavy construction projects for schools and government buildings. He's built his reputation on quality work and reliability.
                </p>
              </div>
              
              <div className="bg-red-50 p-6 rounded-lg border-l-4 border-red-600">
                <h3 className="text-xl font-semibold mb-3 text-gray-900">The Problem</h3>
                <p className="text-gray-700 mb-3">
                  Every Thursday, the same nightmare: his workers need their wages by Friday, or they'll have to leave. He scrambles through stacks of receipts, looking for payments that haven't come through yet.
                </p>
                <p className="text-gray-700 mb-3">
                  He rushes to the school to request expedited payment. But the school administration scolds him—his receipts don't have enough information. They need proper invoices with complete details.
                </p>
                <p className="text-gray-700">
                  Usually, he'd hire an accountant to create proper invoices. But this time, it's too late. He has to let his workers go and cancel upcoming projects just to save enough cash to survive until payment arrives.
                </p>
              </div>
            </div>

            <div className="bg-gradient-to-br from-gray-100 to-gray-200 p-8 rounded-lg">
              <div className="text-center">
                <div className="w-32 h-32 mx-auto mb-4 bg-gray-300 rounded-full flex items-center justify-center">
                  <span className="text-5xl">👷</span>
                </div>
                <h4 className="text-2xl font-bold mb-2">En Azlan</h4>
                <p className="text-gray-600 italic">"I just want to pay my workers on time..."</p>
              </div>
              
              <div className="mt-8 space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-xs">✕</span>
                  </div>
                  <p className="text-gray-700">Workers leaving by Friday</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-xs">✕</span>
                  </div>
                  <p className="text-gray-700">Receipts rejected by schools</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-xs">✕</span>
                  </div>
                  <p className="text-gray-700">No time for accountant</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-xs">✕</span>
                  </div>
                  <p className="text-gray-700">Projects cancelled</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Solution Section */}
      <div className="bg-gradient-to-b from-blue-600 to-blue-700 py-20 text-white">
        <div className="container mx-auto px-4 max-w-5xl">
          <h2 className="text-4xl font-bold text-center mb-6">
            Introducing AliranTunai
          </h2>
          <p className="text-xl text-center mb-16 text-blue-100">
            Your receipts, transformed into government-compliant e-invoices in seconds
          </p>

          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg">
              <div className="w-14 h-14 bg-white/20 rounded-lg flex items-center justify-center mb-4">
                <FileText className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Snap Your Receipt</h3>
              <p className="text-blue-100">
                Just take a photo of your receipt and send it via WhatsApp or Telegram. That's it.
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg">
              <div className="w-14 h-14 bg-white/20 rounded-lg flex items-center justify-center mb-4">
                <CheckCircle className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-semibold mb-3">AI Verification</h3>
              <p className="text-blue-100">
                Our AI instantly verifies your receipt stamp and extracts all details—amount, date, project info.
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg">
              <div className="w-14 h-14 bg-white/20 rounded-lg flex items-center justify-center mb-4">
                <TrendingUp className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Get Your E-Invoice</h3>
              <p className="text-blue-100">
                Receive a government-compliant e-invoice ready to submit for expedited payment. No accountant needed.
              </p>
            </div>
          </div>

          {/* Benefits */}
          <div className="bg-white rounded-lg p-8 text-gray-900">
            <h3 className="text-2xl font-bold mb-6 text-center">For Contractors Like En Azlan</h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="flex items-start gap-3">
                <Wallet className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1">Pay Workers On Time</h4>
                  <p className="text-gray-600 text-sm">Get your payments expedited with proper documentation. Keep your team happy and working.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1">Government-Compliant</h4>
                  <p className="text-gray-600 text-sm">E-invoices meet all LHDN requirements. Schools and agencies accept them immediately.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <TrendingUp className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1">Instant Processing</h4>
                  <p className="text-gray-600 text-sm">From receipt to e-invoice in under 60 seconds. No more waiting for accountants.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <FileText className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold mb-1">Always Accessible</h4>
                  <p className="text-gray-600 text-sm">View all your claims and e-invoices anytime from your dashboard. Never lose a receipt again.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-20 text-center">
        <div className="container mx-auto px-4 max-w-3xl">
          <h2 className="text-4xl font-bold mb-6 text-gray-900">
            Stop Losing Workers. Start Using AliranTunai.
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Join contractors who are getting paid faster and keeping their projects running smoothly.
          </p>
          <Link 
            to="/login"
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            Start Free Today <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
