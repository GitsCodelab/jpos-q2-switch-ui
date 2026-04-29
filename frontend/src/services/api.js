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
  get: (id) => api.get(`/transactions/${id}`),
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
  run: () => api.post('/settlement/run'),
  getBatches: (params) => api.get('/settlement/batches', { params }),
  getBatch: (batchId) => api.get(`/settlement/batches/${batchId}`),
}

export const dashboardAPI = {
  getSummary: () => api.get('/dashboard/summary'),
  getStatus: () => api.get('/dashboard/status'),
}

export default api
