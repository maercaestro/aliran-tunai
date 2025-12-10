import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { getContractorClaims, markClaimAsPaid } from '../api/workOrders';
import { formatCurrency, formatDateTime, getStatusColor, getStatusIcon, getStatusLabel } from '../utils/formatters';
import { ArrowLeft, Download, CheckCircle, Clock, AlertCircle } from 'lucide-react';

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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading work order...</p>
        </div>
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="mx-auto text-red-500 mb-4" size={48} />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Work Order Not Found</h2>
          <button
            onClick={() => navigate('/')}
            className="text-blue-600 hover:text-blue-700 font-medium"
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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-2"
          >
            <ArrowLeft size={20} />
            <span>Back to Dashboard</span>
          </button>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
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
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">📍 Work Order Information</h2>
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Vendor Name</dt>
                  <dd className="mt-1 text-sm text-gray-900 font-semibold">{receiptData.vendor_name || 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Invoice Date</dt>
                  <dd className="mt-1 text-sm text-gray-900">{receiptData.invoice_date || 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Invoice Number</dt>
                  <dd className="mt-1 text-sm text-gray-900">{receiptData.invoice_number || 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Vendor TIN</dt>
                  <dd className="mt-1 text-sm text-gray-900">{receiptData.vendor_tin || 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Total Amount</dt>
                  <dd className="mt-1 text-2xl font-bold text-gray-900">{formatCurrency(receiptData.total_amount)}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Payment Terms</dt>
                  <dd className="mt-1 text-sm text-gray-900">{receiptData.payment_terms || 'N/A'}</dd>
                </div>
              </dl>
            </div>

            {/* Progress Timeline */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">📊 Progress Timeline</h2>
              <div className="space-y-4">
                <TimelineItem
                  icon={<CheckCircle className="text-green-600" size={20} />}
                  title="Receipt Submitted"
                  time={formatDateTime(claim.submitted_at)}
                  completed={true}
                />
                <TimelineItem
                  icon={hasStamp ? <CheckCircle className="text-green-600" size={20} /> : <AlertCircle className="text-red-600" size={20} />}
                  title="Stamp Verified"
                  time={hasStamp ? formatDateTime(claim.submitted_at) : 'Not verified'}
                  completed={hasStamp}
                  description={claim.stamp_details}
                />
                <TimelineItem
                  icon={claim.invoice_id ? <CheckCircle className="text-green-600" size={20} /> : <Clock className="text-gray-400" size={20} />}
                  title="E-Invoice Generated"
                  time={claim.invoice_id ? formatDateTime(claim.processed_at) : 'Pending'}
                  completed={!!claim.invoice_id}
                />
                <TimelineItem
                  icon={isPaid ? <CheckCircle className="text-green-600" size={20} /> : <Clock className="text-gray-400" size={20} />}
                  title="Payment Received"
                  time={isPaid ? formatDateTime(claim.paid_at) : 'Pending'}
                  completed={isPaid}
                />
              </div>
            </div>

            {/* Items List */}
            {receiptData.items && receiptData.items.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">📦 Items & Services</h2>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="border-b border-gray-200">
                      <tr>
                        <th className="text-left py-2 text-sm font-medium text-gray-700">Description</th>
                        <th className="text-right py-2 text-sm font-medium text-gray-700">Qty</th>
                        <th className="text-right py-2 text-sm font-medium text-gray-700">Unit Price</th>
                        <th className="text-right py-2 text-sm font-medium text-gray-700">Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {receiptData.items.map((item, index) => (
                        <tr key={index}>
                          <td className="py-3 text-sm text-gray-900">{item.description}</td>
                          <td className="py-3 text-sm text-gray-600 text-right">{item.quantity}</td>
                          <td className="py-3 text-sm text-gray-600 text-right">{formatCurrency(item.unit_price)}</td>
                          <td className="py-3 text-sm font-semibold text-gray-900 text-right">{formatCurrency(item.amount)}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="border-t-2 border-gray-300">
                      <tr>
                        <td colSpan="3" className="py-3 text-sm font-semibold text-gray-900 text-right">Subtotal:</td>
                        <td className="py-3 text-sm font-semibold text-gray-900 text-right">{formatCurrency(receiptData.subtotal)}</td>
                      </tr>
                      <tr>
                        <td colSpan="3" className="py-3 text-sm font-semibold text-gray-900 text-right">Tax:</td>
                        <td className="py-3 text-sm font-semibold text-gray-900 text-right">{formatCurrency(receiptData.tax_amount)}</td>
                      </tr>
                      <tr>
                        <td colSpan="3" className="py-3 text-lg font-bold text-gray-900 text-right">Total:</td>
                        <td className="py-3 text-lg font-bold text-gray-900 text-right">{formatCurrency(receiptData.total_amount)}</td>
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
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">📸 Receipt Image</h3>
                <img
                  src={`data:image/jpeg;base64,${claim.receipt_image}`}
                  alt="Receipt"
                  className="w-full rounded-lg border border-gray-200"
                />
              </div>
            )}

            {/* E-Invoice Status */}
            {claim.invoice_id && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">📧 E-Invoice Status</h3>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-xs text-gray-500">Invoice ID</dt>
                    <dd className="text-sm font-mono text-gray-900">{claim.invoice_id}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500">Type</dt>
                    <dd className="text-sm text-gray-900">MyInvois UBL 2.1 Compliant</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500">Generated</dt>
                    <dd className="text-sm text-gray-900">{formatDateTime(claim.processed_at)}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500">Status</dt>
                    <dd>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        isPaid ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {isPaid ? '✅ Paid' : '⏳ Awaiting Payment'}
                      </span>
                    </dd>
                  </div>
                </dl>
                <button
                  onClick={handleDownloadEInvoice}
                  className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                >
                  <Download size={18} />
                  Download E-Invoice JSON
                </button>
              </div>
            )}

            {/* Actions */}
            {!isPaid && claim.invoice_id && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">💰 Payment Actions</h3>
                <button
                  onClick={() => markPaidMutation.mutate(claim._id)}
                  disabled={markPaidMutation.isPending}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition disabled:opacity-50"
                >
                  <CheckCircle size={18} />
                  {markPaidMutation.isPending ? 'Processing...' : 'Mark as Paid'}
                </button>
              </div>
            )}

            {isPaid && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="text-green-600 mt-0.5" size={20} />
                  <div>
                    <h4 className="font-semibold text-green-900">Payment Received</h4>
                    <p className="text-sm text-green-700 mt-1">
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
      <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${completed ? 'bg-green-50' : 'bg-gray-50'}`}>
        {icon}
      </div>
      <div className="flex-1">
        <h4 className={`font-medium ${completed ? 'text-gray-900' : 'text-gray-500'}`}>{title}</h4>
        <p className="text-sm text-gray-600">{time}</p>
        {description && <p className="text-xs text-gray-500 mt-1">{description}</p>}
      </div>
    </div>
  );
}
