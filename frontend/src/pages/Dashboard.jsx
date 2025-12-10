import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getDashboardStats, getContractorClaims } from '../api/workOrders';
import { formatCurrency, formatDate, getStatusColor, getStatusIcon, getStatusLabel, getTimeRemaining } from '../utils/formatters';
import { FileText, Clock, CheckCircle, DollarSign, AlertCircle, LogOut, Search } from 'lucide-react';
import { useState } from 'react';

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: getDashboardStats,
  });

  const { data: claims, isLoading: claimsLoading } = useQuery({
    queryKey: ['contractorClaims'],
    queryFn: getContractorClaims,
  });

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Group claims by status
  const activeOrders = claims?.filter(c => c.status === 'active') || [];
  const pendingCompletion = claims?.filter(c => c.status === 'pending_completion') || [];
  const pendingPayment = claims?.filter(c => c.payment_status === 'pending') || [];
  const completedThisMonth = claims?.filter(c => 
    c.status === 'completed' && 
    new Date(c.processed_at).getMonth() === new Date().getMonth()
  ) || [];

  // Filter claims based on search
  const filteredClaims = claims?.filter(claim => 
    claim.claim_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    claim.receipt_data?.vendor_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    claim.invoice_id?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  if (statsLoading || claimsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
            <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <img src="/final-logo.png" alt="AliranTunai ERP" className="h-10 object-contain drop-shadow-[0_0_10px_rgba(45,212,191,0.2)]" />
              <div className="hidden sm:block border-l border-slate-700 pl-4">
                <p className="text-xs text-slate-500 uppercase tracking-wider">Command Center</p>
                <p className="font-semibold text-slate-200">{user?.owner_name || user?.name}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
            >
              <LogOut size={18} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <StatsCard
            icon={<FileText className="text-green-600" size={24} />}
            title="Active Jobs"
            value={activeOrders.length}
            bgColor="bg-green-50"
            borderColor="border-green-200"
          />
          <StatsCard
            icon={<Clock className="text-yellow-600" size={24} />}
            title="Pending Completion"
            value={pendingCompletion.length}
            bgColor="bg-yellow-50"
            borderColor="border-yellow-200"
          />
          <StatsCard
            icon={<DollarSign className="text-blue-600" size={24} />}
            title="Awaiting Payment"
            value={pendingPayment.length}
            bgColor="bg-blue-50"
            borderColor="border-blue-200"
          />
          <StatsCard
            icon={<CheckCircle className="text-gray-600" size={24} />}
            title="Completed This Month"
            value={completedThisMonth.length}
            bgColor="bg-gray-50"
            borderColor="border-gray-200"
          />
          <StatsCard
            icon={<FileText className="text-indigo-600" size={24} />}
            title="E-Invoices Generated"
            value={claims?.filter(c => c.invoice_id).length || 0}
            bgColor="bg-indigo-50"
            borderColor="border-indigo-200"
          />
          <StatsCard
            icon={<DollarSign className="text-green-600" size={24} />}
            title="Paid This Month"
            value={formatCurrency(
              claims?.filter(c => 
                c.payment_status === 'paid' && 
                new Date(c.paid_at).getMonth() === new Date().getMonth()
              ).reduce((sum, c) => sum + (c.receipt_data?.total_amount || 0), 0) || 0
            )}
            bgColor="bg-green-50"
            borderColor="border-green-200"
          />
        </div>

        {/* Work Orders Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">📋 Work Orders & Claims</h2>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                placeholder="Search orders..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            {filteredClaims.length === 0 ? (
              <div className="text-center py-12">
                <AlertCircle className="mx-auto text-gray-400 mb-4" size={48} />
                <p className="text-gray-600">No work orders found</p>
                <p className="text-sm text-gray-500 mt-2">Submit a receipt via WhatsApp to create a claim</p>
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Order ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vendor</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payment</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredClaims.map((claim) => (
                    <tr
                      key={claim._id}
                      onClick={() => navigate(`/work-order/${claim._id}`)}
                      className="hover:bg-gray-50 cursor-pointer transition"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(claim.verification_status || 'active')}`}>
                          {getStatusIcon(claim.verification_status || 'active')} {getStatusLabel(claim.verification_status || 'active')}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {claim.claim_id || claim.invoice_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {claim.receipt_data?.vendor_name || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {formatDate(claim.submitted_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                        {formatCurrency(claim.receipt_data?.total_amount)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          claim.payment_status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {claim.payment_status === 'paid' ? '✅ Paid' : '⏳ Pending'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function StatsCard({ icon, title, value, bgColor, borderColor }) {
  return (
    <div className={`${bgColor} border ${borderColor} rounded-lg p-6`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${bgColor}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}
