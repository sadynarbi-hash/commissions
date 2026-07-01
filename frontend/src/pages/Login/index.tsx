import { useState } from 'react'
import { Form, Input, Button, Typography, Alert } from 'antd'
import { MailOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { apiLogin } from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'

const { Title, Text } = Typography

export default function Login() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { login } = useAuth()
  const navigate = useNavigate()

  const onFinish = async (values: { email: string; password: string }) => {
    setError(null)
    setLoading(true)
    try {
      const data = await apiLogin(values.email.trim(), values.password)
      login(data.access_token, data.user)
      navigate('/', { replace: true })
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Erreur de connexion')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex' }}>

      {/* Panneau gauche — visuel produit */}
      <div style={{
        flex: 1,
        background: 'linear-gradient(160deg, #0A2A0D 0%, #0D3B12 50%, #1B5E20 100%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 32px',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Cercle décoratif */}
        <div style={{
          position: 'absolute',
          width: 500,
          height: 500,
          borderRadius: '50%',
          background: 'rgba(249,168,37,0.05)',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none',
        }} />

        <img
          src="/logo-nma.png"
          alt="NMA"
          style={{ height: 60, objectFit: 'contain', marginBottom: 40 }}
          onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
        />

        <img
          src="/product-sac.png"
          alt="Produit NMA"
          style={{
            maxHeight: 380,
            maxWidth: '100%',
            objectFit: 'contain',
            filter: 'drop-shadow(0 20px 40px rgba(0,0,0,0.5))',
            zIndex: 1,
          }}
          onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
        />

        <div style={{ marginTop: 32, textAlign: 'center', zIndex: 1 }}>
          <Text style={{ color: '#F9A825', fontSize: 18, fontWeight: 700, display: 'block' }}>
            Nouvelle Minoterie Africaine
          </Text>
          <Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, marginTop: 6, display: 'block' }}>
            Gestion des Commissions Commerciales 2026
          </Text>
        </div>
      </div>

      {/* Panneau droit — formulaire */}
      <div style={{
        width: 420,
        background: '#fff',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 40px',
      }}>
        <div style={{ width: '100%', maxWidth: 340 }}>
          <Title level={3} style={{ margin: '0 0 6px', color: '#1B5E20' }}>
            Connexion
          </Title>
          <Text style={{ color: '#888', fontSize: 13, display: 'block', marginBottom: 32 }}>
            Bienvenue — connectez-vous pour continuer
          </Text>

          {error && (
            <Alert
              message={error}
              type="error"
              showIcon
              style={{ marginBottom: 20 }}
            />
          )}

          <Form
            layout="vertical"
            onFinish={onFinish}
            requiredMark={false}
            size="large"
          >
            <Form.Item
              name="email"
              label={<span style={{ color: '#444', fontWeight: 600 }}>Email</span>}
              rules={[{ required: true, message: 'Email requis' }, { type: 'email', message: 'Email invalide' }]}
            >
              <Input
                prefix={<MailOutlined style={{ color: '#bbb' }} />}
                placeholder="votre@email.com"
                autoComplete="email"
              />
            </Form.Item>

            <Form.Item
              name="password"
              label={<span style={{ color: '#444', fontWeight: 600 }}>Mot de passe</span>}
              rules={[{ required: true, message: 'Mot de passe requis' }]}
              style={{ marginBottom: 28 }}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: '#bbb' }} />}
                placeholder="••••••••"
                autoComplete="current-password"
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                style={{
                  background: 'linear-gradient(90deg, #1B5E20, #2E7D32)',
                  borderColor: 'transparent',
                  height: 46,
                  fontSize: 15,
                  fontWeight: 600,
                  borderRadius: 8,
                }}
              >
                Se connecter
              </Button>
            </Form.Item>
          </Form>

          <Text style={{ color: '#ccc', fontSize: 11, display: 'block', textAlign: 'center', marginTop: 40 }}>
            © NMA 2026
          </Text>
        </div>
      </div>
    </div>
  )
}
