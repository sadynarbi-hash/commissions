import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import frFR from 'antd/locale/fr_FR'
import dayjs from 'dayjs'
import 'dayjs/locale/fr'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import AppLayout from './components/AppLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Employees from './pages/Employees'
import Objectives from './pages/Objectives'
import Bonuses from './pages/Bonuses'
import CriteriaForm from './pages/CriteriaForm'
import Ventes from './pages/Ventes'
import Sync from './pages/Sync'
import Settings from './pages/Settings'

dayjs.locale('fr')

function PrivateRoutes() {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/employees" element={<Employees />} />
        <Route path="/objectives" element={<Objectives />} />
        <Route path="/bonuses" element={<Bonuses />} />
        <Route path="/criteria" element={<CriteriaForm />} />
        <Route path="/ventes" element={<Ventes />} />
        <Route path="/sync" element={<Sync />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  )
}

export default function App() {
  return (
    <ConfigProvider
      locale={frFR}
      theme={{
        token: {
          colorPrimary:        '#1B5E20',
          colorSuccess:        '#2E7D32',
          colorWarning:        '#F9A825',
          colorError:          '#C62828',
          colorLink:           '#1B5E20',
          borderRadius:        6,
          fontFamily:          "'Segoe UI', Arial, sans-serif",
        },
        components: {
          Menu: {
            darkItemBg:             '#0D3B12',
            darkItemSelectedBg:     '#1B5E20',
            darkItemHoverBg:        '#164D18',
            darkItemSelectedColor:  '#F9A825',
          },
          Button: { colorPrimary: '#1B5E20' },
          Tag:    { colorPrimary: '#1B5E20' },
        },
      }}
    >
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginRedirect />} />
            <Route path="/*" element={<PrivateRoutes />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ConfigProvider>
  )
}

function LoginRedirect() {
  const { token } = useAuth()
  if (token) return <Navigate to="/" replace />
  return <Login />
}
