import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach token if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bharatshield_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: async (merchantId = 'MER_razorpay_001', password = 'demo123') => {
    const res = await api.post('/auth/login', { merchant_id: merchantId, password });
    if (res.data.access_token) {
      localStorage.setItem('bharatshield_token', res.data.access_token);
      localStorage.setItem('bharatshield_merchant', res.data.merchant_id);
    }
    return res.data;
  },
};

export const transactionsAPI = {
  scoreTransaction: async (data) => {
    const res = await api.post('/transactions/score', data);
    return res.data;
  },
  listTransactions: async (params = {}) => {
    const res = await api.get('/transactions', { params });
    return res.data;
  },
  getTransaction: async (id) => {
    const res = await api.get(`/transactions/${id}`);
    return res.data;
  },
  getRelated: async (id) => {
    const res = await api.get(`/transactions/${id}/related`);
    return res.data;
  },
};

export const analyticsAPI = {
  getOverview: async (merchantId) => {
    const res = await api.get('/analytics/overview', { params: { merchant_id: merchantId } });
    return res.data;
  },
  getTrends: async (merchantId) => {
    const res = await api.get('/analytics/trends', { params: { merchant_id: merchantId } });
    return res.data;
  },
  getModelMetrics: async () => {
    const res = await api.get('/analytics/model');
    return res.data;
  },
};

export const alertsAPI = {
  listAlerts: async (merchantId) => {
    const res = await api.get('/alerts', { params: { merchant_id: merchantId } });
    return res.data;
  },
  acknowledgeAlert: async (id, notes = '') => {
    const res = await api.put(`/alerts/${id}/acknowledge`, { notes });
    return res.data;
  },
  checkSpikes: async (merchantId) => {
    const res = await api.post('/alerts/check-spikes', null, { params: { merchant_id: merchantId } });
    return res.data;
  },
};

export const assistantAPI = {
  ask: async (query) => {
    const res = await api.post('/assistant/ask', { query });
    return res.data;
  },
};

export default api;
