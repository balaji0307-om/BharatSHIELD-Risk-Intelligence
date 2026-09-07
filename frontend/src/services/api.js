import axios from 'axios';

const rawBase = import.meta.env?.VITE_API_URL || '';
// Ensure baseURL points to /api without double slashes
const apiBase = rawBase ? `${rawBase.replace(/\/+$/, '')}/api` : '/api';

const api = axios.create({
  baseURL: apiBase,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach token from localStorage or sessionStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bharatshield_token') || sessionStorage.getItem('bharatshield_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  signup: async ({ email, password, merchantName, captchaToken }) => {
    const res = await api.post('/auth/signup', {
      email,
      password,
      merchant_name: merchantName,
      captcha_token: captchaToken
    });
    return res.data;
  },
  login: async ({ email, merchantId, password, rememberMe, captchaToken }) => {
    const res = await api.post('/auth/login', {
      email,
      merchant_id: merchantId,
      password,
      remember_me: rememberMe,
      captcha_token: captchaToken
    });
    return res.data;
  },
  refresh: async (refreshToken) => {
    const res = await api.post('/auth/refresh', { refresh_token: refreshToken });
    return res.data;
  },
  logout: async () => {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      // Ignore network errors on logout
    } finally {
      localStorage.removeItem('bharatshield_token');
      localStorage.removeItem('bharatshield_refresh_token');
      localStorage.removeItem('bharatshield_user');
      sessionStorage.removeItem('bharatshield_token');
      sessionStorage.removeItem('bharatshield_refresh_token');
      sessionStorage.removeItem('bharatshield_user');
    }
  },
  getMe: async () => {
    const res = await api.get('/auth/me');
    return res.data;
  },
  forgotPassword: async (email) => {
    const res = await api.post('/auth/forgot-password', { email });
    return res.data;
  },
  resetPassword: async (resetToken, newPassword) => {
    const res = await api.post('/auth/reset-password', {
      reset_token: resetToken,
      new_password: newPassword
    });
    return res.data;
  }
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

export const postureAPI = {
  getPosture: async () => {
    const res = await api.get('/merchant/posture');
    return res.data;
  },
};

export const threatsAPI = {
  getLive: async (limit = 20) => {
    const res = await api.get(`/threats/live?limit=${limit}`);
    return res.data;
  },
};

export const fraudNetworkAPI = {
  getNetwork: async () => {
    const res = await api.get('/fraud-network');
    return res.data;
  },
  getTransactionNetwork: async (transactionId) => {
    const res = await api.get(`/fraud-network/${transactionId}`);
    return res.data;
  },
};

export const casesAPI = {
  listCases: async (params = {}) => {
    const res = await api.get('/cases', { params });
    return res.data;
  },
  getCase: async (caseId) => {
    const res = await api.get(`/cases/${caseId}`);
    return res.data;
  },
  updateCase: async (caseId, data) => {
    const res = await api.put(`/cases/${caseId}`, data);
    return res.data;
  },
};

export const simulatorAPI = {
  assess: async (data) => {
    const res = await api.post('/simulator/assess', data);
    return res.data;
  },
};

export const auditAPI = {
  getLogs: async (params = {}) => {
    const res = await api.get('/audit/logs', { params });
    return res.data;
  },
  verifyChain: async () => {
    const res = await api.get('/audit/verify');
    return res.data;
  },
  getLogDetail: async (logId) => {
    const res = await api.get(`/audit/logs/${logId}`);
    return res.data;
  },
};

export default api;
