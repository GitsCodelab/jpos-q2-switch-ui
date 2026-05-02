import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('username')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }),
}

export const transactionAPI = {
  list: (params) => api.get('/transactions', { params }),
  search: (params) => api.get('/transactions/search', { params }),
  get: (id) => api.get(`/transactions/${id}`),
  getEvents: (id) => api.get(`/transactions/${id}/events`),
  create: (data) => api.post('/transactions', data),
}

export const reconciliationAPI = {
  getIssues: (params) => api.get('/reconciliation/issues', { params }),
  getMissing: (params) => api.get('/reconciliation/missing', { params }),
  getReversalCandidates: (params) =>
    api.get('/reconciliation/reversal-candidates', { params }),
  getSummary: () => api.get('/reconciliation/summary'),
}

export const settlementAPI = {
  run: (params) => api.post('/settlement/run', null, { params }),
  getBatches: (params) => api.get('/settlement/batches', { params }),
  getBatch: (batchId) => api.get(`/settlement/batches/${batchId}`),
}

export const dashboardAPI = {
  getSummary: () => api.get('/dashboard/summary'),
  getStatus: (params) => api.get('/dashboard/status', { params }),
  getVolume: () => api.get('/dashboard/volume'),
}

export const netSettlementAPI = {
  list: (params) => api.get('/net-settlement', { params }),
  getSummary: () => api.get('/net-settlement/summary'),
  getByBatch: (batchId) => api.get(`/net-settlement/${batchId}`),
}

export const configAPI = {
  listBins: (params) => api.get('/bins', { params }),
  listTerminals: (params) => api.get('/terminals', { params }),
  getRoutingDecision: (pan) => api.get(`/routing/${pan}`),
}

export const fraudAPI = {
  getDashboard: () => api.get('/fraud/dashboard'),
  getAlerts: (params) => api.get('/fraud/alerts', { params }),
  actionAlert: (id, data) => api.post(`/fraud/alerts/${id}/action`, data),
  getRules: () => api.get('/fraud/rules'),
  createRule: (data) => api.post('/fraud/rules', data),
  getBlacklist: () => api.get('/fraud/blacklist'),
  createBlacklist: (data) => api.post('/fraud/blacklist', data),
  runCheck: (data) => api.post('/fraud/check', data),
  getCases: () => api.get('/fraud/cases'),
  createCase: (data) => api.post('/fraud/cases', data),
  updateCase: (id, data) => api.patch(`/fraud/cases/${id}`, data),
  updateCaseStatus: (id, status) => api.patch(`/fraud/cases/${id}/status`, { status }),
  deleteCase: (id) => api.delete(`/fraud/cases/${id}`),
  getFlaggedTransactions: (params) => api.get('/fraud/flagged-transactions', { params }),
  getDashboardTrends: (params) => api.get('/fraud/dashboard/trends', { params }),
  getDashboardBreakdown: () => api.get('/fraud/dashboard/breakdown'),
  getCaseTimeline: (id) => api.get(`/fraud/cases/${id}/timeline`),
  getAuditLog: (params) => api.get('/fraud/audit-log', { params }),
}

export const testingAPI = {
  getProfiles: () => api.get('/api/v1/testing/profiles'),
  send: (payload) => api.post('/api/v1/testing/send', payload),
  getHistory: (limit = 20) => api.get('/api/v1/testing/history', { params: { limit } }),
}

export const validationAPI = {
  getRules:       (params) => api.get('/validation/rules', { params }),
  createRule:     (data)   => api.post('/validation/rules', data),
  updateRule:     (id, data) => api.patch(`/validation/rules/${id}`, data),
  deleteRule:     (id)     => api.delete(`/validation/rules/${id}`),
  getAuthRules:   (params) => api.get('/validation/auth-rules', { params }),
  createAuthRule: (data)   => api.post('/validation/auth-rules', data),
  updateAuthRule: (id, data) => api.patch(`/validation/auth-rules/${id}`, data),
  deleteAuthRule: (id)     => api.delete(`/validation/auth-rules/${id}`),
  getEvents:      (params) => api.get('/validation/events', { params }),
  getStats:       ()       => api.get('/validation/stats'),
}

export default api
