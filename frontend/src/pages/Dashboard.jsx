import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getDashboardStats, getContractorClaims } from '../api/workOrders';
import { formatCurrency, formatDate, getStatusColor, getStatusIcon, getStatusLabel, getTimeRemaining } from '../utils/formatters';
import { DocumentTextIcon, ClockIcon, CheckCircleIcon, CurrencyDollarIcon, ExclamationCircleIcon, ArrowRightOnRectangleIcon, MagnifyingGlassIcon, HomeIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';
import brandConfig from '../config/brand';

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: getDashboardStats,
  });

  console.log('Dashboard stats:', stats); // Debug log

  const { data: claims, isLoading: claimsLoading } = useQuery({
    queryKey: ['contractorClaims'],
    queryFn: getContractorClaims,
  });

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  // Group claims by status
  const activeOrders = claims?.filter(c => c.status === 'approved' || c.status === 'active') || [];
  const pendingCompletion = claims?.filter(c => c.status === 'pending' || c.status === 'pending_completion') || [];
  const pendingPayment = claims?.filter(c => c.payment_status === 'pending') || [];
  const completedThisMonth = claims?.filter(c => 
    (c.status === 'completed' || c.payment_status === 'paid') && 
    c.processed_at &&
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
      <div className="min-h-screen bg-[var(--brand-bg-from)] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-4"></div>
          <p className="text-[var(--brand-text-secondary)]">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--brand-bg-from)]">
      {/* Header */}
            <header className="bg-[var(--brand-card-bg)]/80 backdrop-blur-md border-b border-[var(--brand-card-bg-hover)] sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <img src={brandConfig.logo.path} alt={brandConfig.logo.alt} className="h-10 object-contain drop-shadow-[0_0_10px_rgba(45,212,191,0.2)]" />
              <div className="hidden sm:block border-l border-white/10 pl-4">
                <p className="text-xs text-[var(--brand-text-secondary)] uppercase tracking-wider">Command Center</p>
                <p className="font-semibold text-[var(--brand-text-primary)]">{user?.owner_name || user?.name}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-2 px-4 py-2 text-[var(--brand-text-secondary)] hover:text-teal-400 hover:bg-teal-500/10 rounded-lg transition"
              >
                <HomeIcon className="w-4.5 h-4.5" />
                <span className="hidden sm:inline">Home</span>
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 text-[var(--brand-text-secondary)] hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition"
              >
                <ArrowRightOnRectangleIcon className="w-4.5 h-4.5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <StatsCard
            icon={<DocumentTextIcon className="text-teal-400 w-6 h-6" />}
            title="Active Jobs"
            value={activeOrders.length}
            bgColor="bg-[var(--brand-card-bg)]"
            borderColor="border-[var(--brand-card-bg-hover)]"
          />
          <StatsCard
            icon={<ClockIcon className="text-amber-400 w-6 h-6" />}
            title="Pending Completion"
            value={pendingCompletion.length}
            bgColor="bg-[var(--brand-card-bg)]"
            borderColor="border-[var(--brand-card-bg-hover)]"
          />
          <StatsCard
            icon={<CurrencyDollarIcon className="text-blue-400 w-6 h-6" />}
            title="Awaiting Payment"
            value={pendingPayment.length}
            bgColor="bg-[var(--brand-card-bg)]"
            borderColor="border-[var(--brand-card-bg-hover)]"
          />
          <StatsCard
            icon={<CheckCircleIcon className="text-[var(--brand-text-secondary)] w-6 h-6" />}
            title="Completed This Month"
            value={completedThisMonth.length}
            bgColor="bg-[var(--brand-card-bg)]"
            borderColor="border-[var(--brand-card-bg-hover)]"
          />
          <StatsCard
            icon={<DocumentTextIcon className="text-indigo-400 w-6 h-6" />}
            title="E-Invoices Generated"
            value={claims?.filter(c => c.invoice_id).length || 0}
            bgColor="bg-[var(--brand-card-bg)]"
            borderColor="border-[var(--brand-card-bg-hover)]"
          />
          <StatsCard
            icon={<CurrencyDollarIcon className="text-teal-400 w-6 h-6" />}
            title="Paid This Month"
            value={formatCurrency(
              claims?.filter(c => 
                c.payment_status === 'paid' && 
                new Date(c.paid_at).getMonth() === new Date().getMonth()
              ).reduce((sum, c) => sum + (c.receipt_data?.total_amount || 0), 0) || 0
            )}
            bgColor="bg-[var(--brand-card-bg)]"
            borderColor="border-[var(--brand-card-bg-hover)]"
          />
        </div>

        {/* Work Orders Section */}
        <div className="bg-[var(--brand-card-bg)] rounded-lg shadow-sm border border-[var(--brand-card-bg-hover)]">
          <div className="px-6 py-4 border-b border-[var(--brand-card-bg-hover)] flex justify-between items-center">
            <h2 className="text-xl font-semibold text-[var(--brand-text-primary)]">📋 Work Orders & Claims</h2>
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[var(--brand-text-secondary)] w-4.5 h-4.5" />
              <input
                type="text"
                placeholder="Search orders..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 bg-[var(--brand-bg-from)] border border-white/10 rounded-lg focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 text-[var(--brand-text-primary)] placeholder-[var(--brand-text-secondary)]"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            {filteredClaims.length === 0 ? (
              <div className="text-center py-12">
                <ExclamationCircleIcon className="mx-auto text-[var(--brand-text-secondary)] mb-4 w-12 h-12" />
                <p className="text-[var(--brand-text-secondary)]">No work orders found</p>
                <p className="text-sm text-[var(--brand-text-secondary)] mt-2">Submit a receipt via WhatsApp to create a claim</p>
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-[var(--brand-bg-from)]/50 border-b border-[var(--brand-card-bg-hover)]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Order ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Vendor</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Payment</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--brand-card-bg-hover)]">
                  {filteredClaims.map((claim) => (
                    <tr
                      key={claim._id}
                      onClick={() => navigate(`/work-order/${claim._id}`)}
                      className="hover:bg-[var(--brand-card-bg-hover)]/50 cursor-pointer transition"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(claim.verification_status || 'active')}`}>
                          {getStatusIcon(claim.verification_status || 'active')} {getStatusLabel(claim.verification_status || 'active')}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-[var(--brand-text-primary)]">
                        {claim.claim_id || claim.invoice_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--brand-text-primary)]">
                        {claim.receipt_data?.vendor_name || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--brand-text-secondary)]">
                        {formatDate(claim.submitted_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-[var(--brand-text-primary)]">
                        {formatCurrency(claim.receipt_data?.total_amount)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          claim.payment_status === 'paid' ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        }`}>
                          {claim.payment_status === 'paid' ? (
                            <span className="flex items-center gap-1">
                              <CheckCircleIcon className="w-3.5 h-3.5" /> Paid
                            </span>
                          ) : (
                            <span className="flex items-center gap-1">
                              <ClockIcon className="w-3.5 h-3.5" /> Pending
                            </span>
                          )}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

        {/* Recent Transactions Section */}
        {stats?.recentTransactions && stats.recentTransactions.length > 0 && (
          <div className="bg-[var(--brand-card-bg)] rounded-lg shadow-sm border border-[var(--brand-card-bg-hover)] mt-8">
            <div className="px-6 py-4 border-b border-[var(--brand-card-bg-hover)]">
              <h2 className="text-xl font-semibold text-[var(--brand-text-primary)]">💰 Recent Transactions</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[var(--brand-bg-from)]/50 border-b border-[var(--brand-card-bg-hover)]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Description</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Category</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--brand-card-bg-hover)]">
                  {stats.recentTransactions.map((transaction) => (
                    <tr key={transaction._id} className="hover:bg-[var(--brand-card-bg-hover)]/50 transition">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--brand-text-secondary)]">
                        {new Date(transaction.timestamp).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          transaction.action === 'sale' ? 'bg-teal-500/10 text-teal-400' :
                          transaction.action === 'purchase' ? 'bg-blue-500/10 text-blue-400' :
                          'bg-[var(--brand-text-secondary)]/10 text-[var(--brand-text-secondary)]'
                        }`}>
                          {transaction.action || 'N/A'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-[var(--brand-text-primary)]">
                        {formatCurrency(transaction.amount)}
                      </td>
                      <td className="px-6 py-4 text-sm text-[var(--brand-text-primary)]">
                        {transaction.description || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--brand-text-secondary)]">
                        {transaction.category || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
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
          <p className="text-sm font-medium text-[var(--brand-text-secondary)] mb-1">{title}</p>
          <p className="text-3xl font-bold text-[var(--brand-text-primary)]">{value}</p>
        </div>
        <div className={`p-3 rounded-lg bg-[var(--brand-bg-from)]/50`}>
          {icon}
        </div>
      </div>
    </div>
  );
}
