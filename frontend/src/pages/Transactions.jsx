import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getContractorClaims } from '../api/workOrders';
import { formatCurrency, formatDate } from '../utils/formatters';
import { ArrowRightOnRectangleIcon, MagnifyingGlassIcon, HomeIcon, ArrowLeftIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { useState, useMemo } from 'react';
import brandConfig from '../config/brand';

export default function Transactions() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all'); // 'all', 'income', 'purchase'

  // Use infinite query for pagination
  const {
    data,
    isLoading: claimsLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['contractorClaims', user?.wa_id],
    queryFn: ({ pageParam = 1 }) => getContractorClaims(user?.wa_id, pageParam),
    enabled: !!user?.wa_id,
    getNextPageParam: (lastPage) => {
      if (lastPage.pagination.hasMore) {
        return lastPage.pagination.currentPage + 1;
      }
      return undefined;
    },
    staleTime: 2 * 60 * 1000, // Data stays fresh for 2 minutes
    cacheTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Flatten all pages into a single array
  const allTransactions = useMemo(() => {
    return data?.pages.flatMap(page => page.transactions) || [];
  }, [data]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const exportToExcel = () => {
    // Prepare data for export
    const dataToExport = filteredTransactions.map(txn => {
      const dateValue = txn.timestamp || txn.date_created || txn.created_at;
      return {
        'Date': dateValue ? formatDate(dateValue) : 'N/A',
        'Type': txn.action || 'Transaction',
        'Description': txn.description || txn.items || 'N/A',
        'Vendor/Customer': txn.vendor || txn.customer || 'N/A',
        'Amount': txn.amount || 0,
        'Category': txn.category || 'Uncategorized'
      };
    });

    // Convert to CSV format
    const headers = Object.keys(dataToExport[0]);
    const csvContent = [
      headers.join(','),
      ...dataToExport.map(row => 
        headers.map(header => {
          const value = row[header];
          // Escape commas and quotes in values
          const escaped = String(value).replace(/"/g, '""');
          return `"${escaped}"`;
        }).join(',')
      )
    ].join('\n');

    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `transactions_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Filter transactions based on search and type
  const filteredTransactions = allTransactions?.filter(claim => {
    // Search filter
    const matchesSearch = claim.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      claim.vendor?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      claim.customer?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      claim.category?.toLowerCase().includes(searchQuery.toLowerCase());
    
    // Type filter
    const matchesType = filterType === 'all' ? true :
      filterType === 'income' ? (claim.action === 'sale' || claim.action === 'income') :
      filterType === 'purchase' ? (claim.action === 'purchase' || claim.action === 'expense') :
      true;
    
    return matchesSearch && matchesType;
  }) || [];

  const totalCount = data?.pages[0]?.pagination?.totalCount || 0;

  if (claimsLoading) {
    return (
      <div className="min-h-screen bg-[var(--brand-bg-from)] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-4"></div>
          <p className="text-[var(--brand-text-secondary)]">Loading transactions...</p>
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
                <p className="text-xs text-[var(--brand-text-secondary)] uppercase tracking-wider">All Transactions</p>
                <p className="font-semibold text-[var(--brand-text-primary)]">{user?.name || user?.owner_name || 'My Account'}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/dashboard')}
                className="flex items-center gap-2 px-4 py-2 text-[var(--brand-text-secondary)] hover:text-teal-400 hover:bg-teal-500/10 rounded-lg transition"
              >
                <ArrowLeftIcon className="w-4.5 h-4.5" />
                <span className="hidden sm:inline">Dashboard</span>
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
        {/* Transactions Table */}
        <div className="bg-[var(--brand-card-bg)] rounded-lg shadow-sm border border-[var(--brand-card-bg-hover)]">
          <div className="px-6 py-4 border-b border-[var(--brand-card-bg-hover)] flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold text-[var(--brand-text-primary)]">All Transactions</h2>
              <p className="text-sm text-[var(--brand-text-secondary)] mt-1">
                {filteredTransactions.length} of {totalCount} transaction{totalCount !== 1 ? 's' : ''} 
                {searchQuery || filterType !== 'all' ? ' (filtered)' : ''}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={exportToExcel}
                disabled={filteredTransactions.length === 0}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 rounded-lg transition border border-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ArrowDownTrayIcon className="w-4.5 h-4.5" />
                <span className="hidden sm:inline">Export CSV</span>
              </button>
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[var(--brand-text-secondary)] w-4.5 h-4.5" />
                <input
                  type="text"
                  placeholder="Search transactions..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 bg-[var(--brand-bg-from)] border border-white/10 rounded-lg focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 text-[var(--brand-text-primary)] placeholder-[var(--brand-text-secondary)]"
                />
              </div>
            </div>
          </div>

          {/* Filter Buttons */}
          <div className="px-6 py-4 border-b border-[var(--brand-card-bg-hover)] flex items-center gap-3">
            <span className="text-sm text-[var(--brand-text-secondary)] font-medium">Filter by:</span>
            <div className="flex gap-2">
              <button
                onClick={() => setFilterType('all')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  filterType === 'all'
                    ? 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
                    : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:bg-slate-800 hover:text-slate-300'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilterType('income')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  filterType === 'income'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:bg-slate-800 hover:text-slate-300'
                }`}
              >
                Income
              </button>
              <button
                onClick={() => setFilterType('purchase')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  filterType === 'purchase'
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:bg-slate-800 hover:text-slate-300'
                }`}
              >
                Purchase
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            {filteredTransactions.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-[var(--brand-text-secondary)]">{searchQuery ? 'No transactions match your search' : 'No transactions yet'}</p>
                <p className="text-sm text-[var(--brand-text-secondary)] mt-2">Send a receipt or invoice via WhatsApp to get started</p>
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-[var(--brand-bg-from)]/50 border-b border-[var(--brand-card-bg-hover)]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Description</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Vendor/Customer</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--brand-text-secondary)] uppercase tracking-wider">Category</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--brand-card-bg-hover)]">
                  {filteredTransactions.map((txn) => (
                    <tr
                      key={txn._id}
                      className="hover:bg-[var(--brand-card-bg-hover)]/50 transition"
                    >
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--brand-text-secondary)]">
                        {formatDate(txn.timestamp || txn.date_created || txn.created_at)}
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
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--brand-text-primary)]">
                        {txn.vendor || txn.customer || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-[var(--brand-text-primary)]">
                        {formatCurrency(txn.amount || 0)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--brand-text-secondary)]">
                        {txn.category || 'Uncategorized'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Load More Button */}
          {hasNextPage && !searchQuery && filterType === 'all' && (
            <div className="px-6 py-4 border-t border-[var(--brand-card-bg-hover)] flex justify-center">
              <button
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
                className="px-6 py-3 bg-teal-500/10 text-teal-400 hover:bg-teal-500/20 rounded-lg transition border border-teal-500/20 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {isFetchingNextPage ? (
                  <span className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-teal-400"></div>
                    Loading more...
                  </span>
                ) : (
                  `Load More (${allTransactions.length} of ${totalCount})`
                )}
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
