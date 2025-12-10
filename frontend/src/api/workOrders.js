import apiClient from './client';

// Get all work orders for current user
export const getWorkOrders = async () => {
  const response = await apiClient.get('/api/work-orders');
  return response.data;
};

// Get single work order by ID
export const getWorkOrder = async (orderId) => {
  const response = await apiClient.get(`/api/work-orders/${orderId}`);
  return response.data;
};

// Create new work order (from WhatsApp log)
export const createWorkOrder = async (orderData) => {
  const response = await apiClient.post('/api/work-orders', orderData);
  return response.data;
};

// Update work order status
export const updateWorkOrderStatus = async (orderId, status) => {
  const response = await apiClient.patch(`/api/work-orders/${orderId}/status`, { status });
  return response.data;
};

// Get dashboard stats
export const getDashboardStats = async () => {
  const response = await apiClient.get('/api/dashboard/stats');
  return response.data;
};

// Get all contractor claims (receipts + e-invoices)
export const getContractorClaims = async () => {
  const response = await apiClient.get('/api/contractor-claims');
  return response.data;
};

// Mark claim as paid
export const markClaimAsPaid = async (claimId) => {
  const response = await apiClient.patch(`/api/contractor-claims/${claimId}/paid`);
  return response.data;
};

// Auth endpoints
export const sendOTP = async (phoneNumber) => {
  const response = await apiClient.post('/api/auth/send-otp', { phone_number: phoneNumber });
  return response.data;
};

export const verifyOTP = async (phoneNumber, otp) => {
  const response = await apiClient.post('/api/auth/verify-otp', { phone_number: phoneNumber, otp });
  return response.data;
};
