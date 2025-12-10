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
    active: 'bg-green-100 text-green-800 border-green-300',
    pending_completion: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    pending_payment: 'bg-blue-100 text-blue-800 border-blue-300',
    completed: 'bg-gray-100 text-gray-800 border-gray-300',
    cancelled: 'bg-red-100 text-red-800 border-red-300',
  };
  return colors[status] || 'bg-gray-100 text-gray-800 border-gray-300';
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
