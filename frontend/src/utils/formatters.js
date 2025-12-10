import { format, formatDistance, parseISO } from 'date-fns';

export const formatDate = (date) => {
  if (!date) return 'N/A';
  try {
    const parsedDate = typeof date === 'string' ? parseISO(date) : date;
    return format(parsedDate, 'dd/MM/yyyy');
  } catch (error) {
    return 'Invalid date';
  }
};

export const formatDateTime = (date) => {
  if (!date) return 'N/A';
  try {
    const parsedDate = typeof date === 'string' ? parseISO(date) : date;
    return format(parsedDate, 'dd/MM/yyyy HH:mm');
  } catch (error) {
    return 'Invalid date';
  }
};

export const formatCurrency = (amount) => {
  if (amount === null || amount === undefined) return 'RM 0.00';
  return `RM ${Number(amount).toLocaleString('en-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

export const getTimeRemaining = (deadline) => {
  if (!deadline) return 'No deadline';
  try {
    const deadlineDate = typeof deadline === 'string' ? parseISO(deadline) : deadline;
    const now = new Date();
    
    if (deadlineDate < now) {
      return 'Overdue';
    }
    
    return formatDistance(deadlineDate, now, { addSuffix: true });
  } catch (error) {
    return 'Invalid deadline';
  }
};

export const getStatusColor = (status) => {
  const colors = {
    active: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
    approved: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
    pending: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    pending_completion: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    pending_payment: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    completed: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    paid: 'bg-green-500/10 text-green-400 border-green-500/20',
    cancelled: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    rejected: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  };
  return colors[status] || 'bg-slate-500/10 text-slate-400 border-slate-500/20';
};

export const getStatusIcon = (status) => {
  const icons = {
    active: '🟢',
    pending_completion: '🟡',
    pending_payment: '🔵',
    completed: '✅',
    cancelled: '❌',
  };
  return icons[status] || '⚪';
};

export const getStatusLabel = (status) => {
  const labels = {
    active: 'Active',
    pending_completion: 'Pending Completion',
    pending_payment: 'Pending Payment',
    completed: 'Completed & Paid',
    cancelled: 'Cancelled',
  };
  return labels[status] || status;
};
