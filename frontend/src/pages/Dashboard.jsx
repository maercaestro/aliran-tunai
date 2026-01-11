import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getDashboardStats } from '../api/workOrders';
import { formatCurrency, formatDate } from '../utils/formatters';
import { DocumentTextIcon, ClockIcon, CheckCircleIcon, CurrencyDollarIcon, ExclamationCircleIcon, ArrowRightOnRectangleIcon, HomeIcon, ArrowTrendingUpIcon, ListBulletIcon } from '@heroicons/react/24/outline';
import brandConfig from '../config/brand';

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboardStats', user?.wa_id],
    queryFn: () => getDashboardStats(user?.wa_id),
    enabled: !!user?.wa_id,
  });

  // Only fetch recent transactions from stats, no need for full list
  const recentTransactions = stats?.recentTransactions?.slice(0, 5) || [];

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (statsLoading) {
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
                <p className="text-xs text-[var(--brand-text-secondary)] uppercase tracking-wider">{user?.mode === 'business' ? 'Business' : 'Personal'} Dashboard</p>
                <p className="font-semibold text-[var(--brand-text-primary)]">{user?.name || user?.owner_name || 'My Transactions'}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/transactions')}
                className="flex items-center gap-2 px-4 py-2 text-[var(--brand-text-secondary)] hover:text-teal-400 hover:bg-teal-500/10 rounded-lg transition"
              >
                <ListBulletIcon className="w-4.5 h-4.5" />
                <span className="hidden sm:inline">Transactions</span>
              </button>
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
            title="Total Transactions"
            value={stats?.totalTransactions || 0}
            bgColor="bg-[var(--brand-card-bg)]"
            borderColor="border-[var(--brand-card-bg-hover)]"
          />
          <StatsCard
            icon={<ArrowTrendingUpIcon className="text-emerald-400 w-6 h-6" />}
            title="Total Income"
            value={formatCurrency(stats?.summary?.totalSales || 0)}
            bgColor="bg-[var(--brand-card-bg)]"
            borderColor="border-[var(--brand-card-bg-hover)]"
          />
          <StatsCard
            icon={<CurrencyDollarIcon className="text-rose-400 w-6 h-6" />}
            title="Total Spending"
            value={formatCurrency(stats?.summary?.totalPurchases || 0)}
            bgColor="bg-[var(--brand-card-bg)]"
            borderColor="border-[var(--brand-card-bg-hover)]"
          />
          <StatsCard
            icon={<ClockIcon className="text-amber-400 w-6 h-6" />}
            title="Cash Conversion Cycle"
            value={`${stats?.ccc || 0} days`}
            bgColor="bg-[var(--brand-card-bg)]"
            borderColor="border-[var(--brand-card-bg-hover)]"
          />
          <StatsCard
            icon={<CheckCircleIcon className="text-blue-400 w-6 h-6" />}
            title="Payments Received"
            value={formatCurrency(stats?.summary?.totalPaymentsReceived || 0)}
            bgColor="bg-[var(--brand-card-bg)]"
            borderColor="border-[var(--brand-card-bg-hover)]"
          />
          <StatsCard
            icon={<CurrencyDollarIcon className="text-indigo-400 w-6 h-6" />}
            title="Payments Made"
            value={formatCurrency(stats?.summary?.totalPaymentsMade || 0)}
            bgColor="bg-[var(--brand-card-bg)]"
            borderColor="border-[var(--brand-card-bg-hover)]"
          />
        </div>

        {/* Recent Transactions */}
        <div className="bg-[var(--brand-card-bg)] rounded-lg shadow-sm border border-[var(--brand-card-bg-hover)]">
          <div className="px-6 py-4 border-b border-[var(--brand-card-bg-hover)] flex justify-between items-center">
            <h2 className="text-xl font-semibold text-[var(--brand-text-primary)]">Recent Transactions</h2>
            <button
              onClick={() => navigate('/transactions')}
              className="flex items-center gap-2 px-4 py-2 bg-teal-500/10 text-teal-400 hover:bg-teal-500/20 rounded-lg transition border border-teal-500/20"
            >
              <ListBulletIcon className="w-4.5 h-4.5" />
              <span>View All</span>
            </button>
          </div>

          <div className="overflow-x-auto">
            {recentTransactions.length === 0 ? (
              <div className="text-center py-12">
                <ExclamationCircleIcon className="mx-auto text-[var(--brand-text-secondary)] mb-4 w-12 h-12" />
                <p className="text-[var(--brand-text-secondary)]">No transactions yet</p>
                <p className="text-sm text-[var(--brand-text-secondary)] mt-2">Send a receipt or invoice via WhatsApp to get started</p>
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-[var(--brand-bg-from)]/50 border-b border-[var(--brand-card-bg-hover)]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Description</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--brand-card-bg-hover)]">
                  {recentTransactions.map((txn) => (
                    <tr key={txn._id} className="hover:bg-[var(--brand-card-bg-hover)]/50 transition">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--brand-text-secondary)]">
                        {formatDate(txn.timestamp || txn.date_created)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${
                          txn.action === 'sale' || txn.action === 'income' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                          txn.action === 'purchase' || txn.action === 'expense' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                          'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                        }`}>
                          {txn.action || 'Transaction'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-[var(--brand-text-primary)]">
                        {txn.description || txn.items || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-[var(--brand-text-primary)]">
                        {formatCurrency(txn.amount || 0)}
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
