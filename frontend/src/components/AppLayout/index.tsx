import { Layout, Menu, Button, Dropdown, Avatar } from 'antd'
import {
  DashboardOutlined,
  TeamOutlined,
  AimOutlined,
  DollarOutlined,
  CheckSquareOutlined,
  BarChartOutlined,
  SyncOutlined,
  SettingOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { ReactNode } from 'react'
import { useAuth } from '../../contexts/AuthContext'

const { Sider, Content, Header } = Layout

// ─── Charte NMA ────────────────────────────────────────────────────────────
const NMA_GREEN  = '#1B5E20'   // vert foncé (texte NMA)
const NMA_GOLD   = '#F9A825'   // or (épi de blé)
const NMA_SIDER  = '#0D3B12'   // vert très foncé pour le fond sidebar

interface Props { children: ReactNode }

const menuItems = [
  { key: '/',           icon: <DashboardOutlined />, label: 'Tableau de bord' },
  { key: '/employees',  icon: <TeamOutlined />,       label: 'Commerciaux' },
  { key: '/objectives', icon: <AimOutlined />,        label: 'Objectifs' },
  { key: '/bonuses',    icon: <DollarOutlined />,        label: 'Commissions' },
  { key: '/criteria',   icon: <CheckSquareOutlined />, label: 'Critères qualitatifs' },
  { key: '/ventes',     icon: <BarChartOutlined />,    label: 'Ventes' },
  { key: '/sync',       icon: <SyncOutlined />,       label: 'Synchronisation' },
  { key: '/settings',   icon: <SettingOutlined />,    label: 'Paramètres' },
]

export default function AppLayout({ children }: Props) {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const { user, logout } = useAuth()

  const userMenu = {
    items: [
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: 'Déconnexion',
        danger: true,
        onClick: () => { logout(); navigate('/login') },
      },
    ],
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        theme="dark"
        style={{
          position: 'fixed', left: 0, top: 0, bottom: 0, zIndex: 100,
          background: NMA_SIDER,
        }}
      >
        {/* Logo NMA */}
        <div style={{
          height: 80,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: `1px solid rgba(249,168,37,0.3)`,
          padding: '8px 12px',
          gap: 6,
        }}>
          <img
            src="/logo-nma.png"
            alt="NMA"
            style={{ height: 52, objectFit: 'contain' }}
            onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
        </div>

        <Menu
          mode="inline"
          selectedKeys={[pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ marginTop: 8, background: 'transparent', borderRight: 'none' }}
          theme="dark"
        />

        <div style={{
          position: 'absolute',
          bottom: 16,
          left: 0,
          right: 0,
          textAlign: 'center',
          color: 'rgba(249,168,37,0.5)',
          fontSize: 11,
        }}>
          © NMA 2026
        </div>
      </Sider>

      <Layout style={{ marginLeft: 200 }}>
        <Header style={{
          background: NMA_GREEN,
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <span style={{ fontSize: 15, fontWeight: 700, color: '#fff', letterSpacing: 0.5 }}>
            Gestion des Commissions Commerciales
          </span>
          <Dropdown menu={userMenu} placement="bottomRight" trigger={['click']}>
            <Button
              type="text"
              style={{ color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}
            >
              <Avatar size={28} icon={<UserOutlined />} style={{ background: '#F9A825', color: '#0D3B12' }} />
              <span style={{ fontSize: 13, fontWeight: 600 }}>{user?.nom}</span>
            </Button>
          </Dropdown>
        </Header>

        <Content style={{
          margin: 24,
          background: '#f4f6f0',
          minHeight: 'calc(100vh - 64px)',
        }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}
