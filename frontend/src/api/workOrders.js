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

// Get dashboard stats for authenticated user
export const getDashboardStats = async (waId) => {
  const response = await apiClient.get(`/api/dashboard/${waId}`);
  return response.data;
};

// Get all transactions (receipts/claims) for authenticated user with pagination
export const getContractorClaims = async (waId, page = 1, limit = 10) => {
  const response = await apiClient.get(`/api/transactions/${waId}?page=${page}&limit=${limit}`);
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
