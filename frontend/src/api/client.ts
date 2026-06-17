import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('nma_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401 && !window.location.pathname.includes('/login')) {
      localStorage.removeItem('nma_token')
      localStorage.removeItem('nma_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

export const apiLogin = (email: string, password: string) =>
  api.post('/auth/login', { email, password }).then(r => r.data)

export const apiGetMe = () =>
  api.get('/auth/me').then(r => r.data)

export const apiChangePassword = (old_password: string, new_password: string) =>
  api.post('/auth/change-password', { old_password, new_password }).then(r => r.data)

export const apiListUsers = () =>
  api.get('/auth/users').then(r => r.data)

export const apiCreateUser = (data: object) =>
  api.post('/auth/users', data).then(r => r.data)

export const apiUpdateUser = (id: number, data: object) =>
  api.patch(`/auth/users/${id}`, data).then(r => r.data)

export const apiResetPassword = (id: number, new_password: string) =>
  api.post(`/auth/users/${id}/reset-password`, { new_password }).then(r => r.data)

// Employees
export const getEmployees = (params?: { actif?: boolean; region_id?: number }) =>
  api.get('/employees', { params }).then(r => r.data)

export const createEmployee = (data: object) =>
  api.post('/employees', data).then(r => r.data)

export const updateEmployee = (id: number, data: object) =>
  api.patch(`/employees/${id}`, data).then(r => r.data)

export const deactivateEmployee = (id: number) =>
  api.delete(`/employees/${id}`)

export const getRegions = () => api.get('/regions').then(r => r.data)
export const createRegion = (data: object) => api.post('/regions', data).then(r => r.data)

// Objectives
export const getObjectives = (params?: { periode?: string; employee_id?: number }) =>
  api.get('/objectives', { params }).then(r => r.data)

export const upsertObjective = (data: object) =>
  api.post('/objectives', data).then(r => r.data)

export const deleteObjective = (id: number) => api.delete(`/objectives/${id}`)

// Forecasts
export const getForecasts = (params?: { periode?: string; employee_id?: number }) =>
  api.get('/forecasts', { params }).then(r => r.data)

export const upsertForecast = (data: object) =>
  api.post('/forecasts', data).then(r => r.data)

// Clients & Portfolio
export const getClients = () => api.get('/clients').then(r => r.data)
export const createClient = (data: object) => api.post('/clients', data).then(r => r.data)
export const getPortfolio = (employeeId: number, annee: number) =>
  api.get(`/portfolio/${employeeId}/${annee}`).then(r => r.data)
export const assignPortfolio = (data: object) => api.post('/portfolio', data).then(r => r.data)

// Bonuses
export const getBonusPeriods = () => api.get('/bonus-periods').then(r => r.data)

export const calculateBonuses = (periode: string, employee_ids?: number[]) =>
  api.post('/bonuses/calculate', { periode, employee_ids }).then(r => r.data)

export const getBonuses = (params?: { periode?: string; employee_id?: number }) =>
  api.get('/bonuses', { params }).then(r => r.data)

export const getBonus = (id: number) => api.get(`/bonuses/${id}`).then(r => r.data)

export const validateBonuses = (periode: string, valide_par: string) =>
  api.post('/bonuses/validate', { periode, valide_par }).then(r => r.data)

export const getManualCriteria = (periode: string) =>
  api.get('/manual-criteria', { params: { periode } }).then(r => r.data)

export const upsertManualCriteria = (data: object) =>
  api.post('/manual-criteria', data).then(r => r.data)

export const exportBonuses = (periode: string) =>
  api.get(`/bonuses/export/${periode}`, { responseType: 'blob' })

export const downloadPV = (bonusId: number) =>
  api.get(`/bonuses/${bonusId}/pv`, { responseType: 'blob' })

export const downloadRecap = (periode: string) =>
  api.get(`/bonuses/recap/${periode}`, { responseType: 'blob' })

// Sync
export const triggerSync = (source: string, periode: string) =>
  api.post('/sync', { source, periode }).then(r => r.data)

export const getSyncLogs = (source?: string) =>
  api.get('/sync/logs', { params: source ? { source } : {} }).then(r => r.data)

export const testConnection = (source: string) =>
  api.post('/sync/test-connection', { source }).then(r => r.data)

// Dashboard
export const getDashboard = (periode: string) =>
  api.get(`/dashboard/${periode}`).then(r => r.data)

export const getVentes = (params?: { periode?: string; region_id?: number; gamme?: string }) =>
  api.get('/ventes', { params }).then(r => r.data)
