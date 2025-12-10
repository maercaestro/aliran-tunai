import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { getContractorClaims, markClaimAsPaid } from '../api/workOrders';
import { formatCurrency, formatDateTime, getStatusColor, getStatusIcon, getStatusLabel } from '../utils/formatters';
import { ArrowLeft, Download, CheckCircle, Clock, AlertCircle, MapPin, ChartBar, Banknote } from 'lucide-react';

export default function WorkOrderDetail() {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: claims, isLoading } = useQuery({
    queryKey: ['contractorClaims'],
    queryFn: getContractorClaims,
  });

  const markPaidMutation = useMutation({
    mutationFn: markClaimAsPaid,
    onSuccess: () => {
      queryClient.invalidateQueries(['contractorClaims']);
      alert('Payment marked as received!');
    },
  });

  const claim = claims?.find(c => c._id === orderId);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-4"></div>
          <p className="text-slate-400">Loading work order...</p>
        </div>
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="mx-auto text-rose-500 mb-4" size={48} />
          <h2 className="text-2xl font-bold text-slate-200 mb-2">Work Order Not Found</h2>
          <button
            onClick={() => navigate('/')}
            className="text-teal-400 hover:text-teal-300 font-medium"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const receiptData = claim.receipt_data || {};
  const hasStamp = claim.has_stamp;
  const isPaid = claim.payment_status === 'paid';

  const handleDownloadEInvoice = () => {
    const dataStr = JSON.stringify(claim.einvoice_json, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${claim.invoice_id || 'invoice'}.json`;
    link.click();
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-slate-400 hover:text-slate-200 mb-2 transition"
          >
            <ArrowLeft size={20} />
            <span>Back to Dashboard</span>
          </button>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-slate-200 tracking-tight">
                Work Order <span className="font-mono text-teal-400">#{claim.claim_id || claim.invoice_id}</span>
              </h1>
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border mt-3 ${getStatusColor(claim.verification_status || 'active')}`}>
                {getStatusIcon(claim.verification_status || 'active')} 
                <span className="uppercase tracking-wider">{getStatusLabel(claim.verification_status || 'active')}</span>
              </span>
            </div>
            <img src="/final-logo.png" alt="AliranTunai" className="h-10 object-contain opacity-80 drop-shadow-[0_0_10px_rgba(45,212,191,0.2)]" />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Main Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Info Card */}
            <div className="bg-slate-900 rounded-lg shadow-sm border border-slate-800 p-6">
              <h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-teal-400" />
                Work Order Information
              </h2>
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-slate-500">Vendor Name</dt>
                  <dd className="mt-1 text-sm text-slate-200 font-semibold">{receiptData.vendor_name || 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-slate-500">Invoice Date</dt>
                  <dd className="mt-1 text-sm text-slate-200">{receiptData.invoice_date || 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-slate-500">Invoice Number</dt>
                  <dd className="mt-1 text-sm text-slate-200">{receiptData.invoice_number || 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-slate-500">Vendor TIN</dt>
                  <dd className="mt-1 text-sm text-slate-200">{receiptData.vendor_tin || 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-slate-500">Total Amount</dt>
                  <dd className="mt-1 text-2xl font-bold text-slate-200">{formatCurrency(receiptData.total_amount)}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-slate-500">Payment Terms</dt>
                  <dd className="mt-1 text-sm text-slate-200">{receiptData.payment_terms || 'N/A'}</dd>
                </div>
              </dl>
            </div>

            {/* Progress Timeline */}
            <div className="bg-slate-900 rounded-lg shadow-sm border border-slate-800 p-6">
              <h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
                <ChartBar className="w-5 h-5 text-teal-400" />
                Progress Timeline
              </h2>
              <div className="space-y-4">
                <TimelineItem
                  icon={<CheckCircle className="text-teal-400" size={20} />}
                  title="Receipt Submitted"
                  time={formatDateTime(claim.submitted_at)}
                  completed={true}
                />
                <TimelineItem
                  icon={<CheckCircle className="text-teal-400" size={20} />}
                  title="Stamp Verified"
                  time={formatDateTime(claim.submitted_at)}
                  completed={true}
                  description="Verified"
                />
                <TimelineItem
                  icon={claim.invoice_id ? <CheckCircle className="text-teal-400" size={20} /> : <Clock className="text-slate-600" size={20} />}
                  title="E-Invoice Generated"
                  time={claim.invoice_id ? formatDateTime(claim.processed_at) : 'Pending'}
                  completed={!!claim.invoice_id}
                />
                <TimelineItem
                  icon={isPaid ? <CheckCircle className="text-teal-400" size={20} /> : <Clock className="text-slate-600" size={20} />}
                  title="Payment Received"
                  time={isPaid ? formatDateTime(claim.paid_at) : 'Pending'}
                  completed={isPaid}
                />
              </div>
            </div>

            {/* Items List */}
            {receiptData.items && receiptData.items.length > 0 && (
              <div className="bg-slate-900 rounded-lg shadow-sm border border-slate-800 p-6">
                <h2 className="text-lg font-semibold text-slate-200 mb-4">📦 Items & Services</h2>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="border-b border-slate-800">
                      <tr>
                        <th className="text-left py-2 text-sm font-medium text-slate-400">Description</th>
                        <th className="text-right py-2 text-sm font-medium text-slate-400">Qty</th>
                        <th className="text-right py-2 text-sm font-medium text-slate-400">Unit Price</th>
                        <th className="text-right py-2 text-sm font-medium text-slate-400">Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {receiptData.items.map((item, index) => (
                        <tr key={index}>
                          <td className="py-3 text-sm text-slate-300">{item.description}</td>
                          <td className="py-3 text-sm text-slate-400 text-right">{item.quantity}</td>
                          <td className="py-3 text-sm text-slate-400 text-right">{formatCurrency(item.unit_price)}</td>
                          <td className="py-3 text-sm font-semibold text-slate-200 text-right">{formatCurrency(item.amount)}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="border-t-2 border-slate-700">
                      <tr>
                        <td colSpan="3" className="py-3 text-sm font-semibold text-slate-300 text-right">Subtotal:</td>
                        <td className="py-3 text-sm font-semibold text-slate-200 text-right">{formatCurrency(receiptData.subtotal)}</td>
                      </tr>
                      <tr>
                        <td colSpan="3" className="py-3 text-sm font-semibold text-slate-300 text-right">Tax:</td>
                        <td className="py-3 text-sm font-semibold text-slate-200 text-right">{formatCurrency(receiptData.tax_amount)}</td>
                      </tr>
                      <tr>
                        <td colSpan="3" className="py-3 text-lg font-bold text-slate-200 text-right">Total:</td>
                        <td className="py-3 text-lg font-bold text-teal-400 text-right">{formatCurrency(receiptData.total_amount)}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Actions & E-Invoice */}
          <div className="space-y-6">
            {/* Receipt Image */}
            {claim.receipt_image && (
              <div className="bg-slate-900 rounded-lg shadow-sm border border-slate-800 p-4">
                <h3 className="text-sm font-semibold text-slate-200 mb-3">📸 Receipt Image</h3>
                <img
                  src={`data:image/jpeg;base64,${claim.receipt_image}`}
                  alt="Receipt"
                  className="w-full rounded-lg border border-slate-700"
                />
              </div>
            )}

            {/* E-Invoice Status */}
            {claim.invoice_id && (
              <div className="bg-slate-900 rounded-lg shadow-sm border border-slate-800 p-6">
                <h3 className="text-sm font-semibold text-slate-200 mb-4">📧 E-Invoice Status</h3>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-xs text-slate-500">Invoice ID</dt>
                    <dd className="text-sm font-mono text-slate-300">{claim.invoice_id}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Type</dt>
                    <dd className="text-sm text-slate-300">MyInvois UBL 2.1 Compliant</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Generated</dt>
                    <dd className="text-sm text-slate-300">{formatDateTime(claim.processed_at)}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Status</dt>
                    <dd>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        isPaid ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}>
                        {isPaid ? (
                          <span className="flex items-center gap-1.5">
                            <CheckCircle className="w-4 h-4" /> Paid
                          </span>
                        ) : (
                          <span className="flex items-center gap-1.5">
                            <Clock className="w-4 h-4" /> Awaiting Payment
                          </span>
                        )}
                      </span>
                    </dd>
                  </div>
                </dl>
                <button
                  onClick={handleDownloadEInvoice}
                  className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition shadow-lg shadow-blue-900/20"
                >
                  <Download size={18} />
                  Download E-Invoice JSON
                </button>
              </div>
            )}

            {/* Actions */}
            {!isPaid && claim.invoice_id && (
              <div className="bg-slate-900 rounded-lg shadow-sm border border-slate-800 p-6">
                <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <Banknote className="w-4 h-4 text-teal-400" />
                  Payment Actions
                </h3>
                <button
                  onClick={() => markPaidMutation.mutate(claim._id)}
                  disabled={markPaidMutation.isPending}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-lg transition disabled:opacity-50 shadow-lg shadow-teal-900/20"
                >
                  <CheckCircle size={18} />
                  {markPaidMutation.isPending ? 'Processing...' : 'Mark as Paid'}
                </button>
              </div>
            )}

            {isPaid && (
              <div className="bg-teal-900/20 border border-teal-900/50 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="text-teal-400 mt-0.5" size={20} />
                  <div>
                    <h4 className="font-semibold text-teal-200">Payment Received</h4>
                    <p className="text-sm text-teal-300/80 mt-1">
                      Payment was received on {formatDateTime(claim.paid_at)}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function TimelineItem({ icon, title, time, completed, description }) {
  return (
    <div className="flex gap-4">
      <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${completed ? 'bg-teal-500/10' : 'bg-slate-800'}`}>
        {icon}
      </div>
      <div className="flex-1">
        <h4 className={`font-medium ${completed ? 'text-slate-200' : 'text-slate-500'}`}>{title}</h4>
        <p className="text-sm text-slate-400">{time}</p>
        {description && <p className="text-xs text-slate-500 mt-1">{description}</p>}
      </div>
    </div>
  );
}
