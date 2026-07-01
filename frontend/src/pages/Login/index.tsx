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

      {/* Panneau gauche — visuel produit sur fond blanc */}
      <div style={{
        flex: 1,
        background: '#ffffff',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 32px',
      }}>
        <img
          src="/product-sac.png"
          alt="Produit NMA"
          style={{
            maxHeight: 460,
            maxWidth: '80%',
            objectFit: 'contain',
          }}
          onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
        />
        <Text style={{ color: '#1B5E20', fontSize: 15, fontWeight: 600, marginTop: 24, display: 'block' }}>
          Nouvelle Minoterie Africaine
        </Text>
        <Text style={{ color: '#888', fontSize: 12, marginTop: 4, display: 'block' }}>
          Gestion des Commissions Commerciales 2026
        </Text>
      </div>

      {/* Panneau droit — formulaire sur fond vert */}
      <div style={{
        width: 420,
        background: 'linear-gradient(160deg, #1B6B2E 0%, #207832 50%, #278039 100%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 40px',
      }}>
        <div style={{ width: '100%', maxWidth: 340 }}>
          <img
            src="/logo-nma.png"
            alt="NMA"
            style={{ height: 48, objectFit: 'contain', marginBottom: 28, display: 'block' }}
            onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
          />

          <Title level={3} style={{ margin: '0 0 6px', color: '#F9A825' }}>
            Connexion
          </Title>
          <Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, display: 'block', marginBottom: 32 }}>
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
              label={<span style={{ color: 'rgba(255,255,255,0.85)', fontWeight: 600 }}>Email</span>}
              rules={[{ required: true, message: 'Email requis' }, { type: 'email', message: 'Email invalide' }]}
            >
              <Input
                prefix={<MailOutlined style={{ color: '#bbb' }} />}
                placeholder="votre@email.com"
                autoComplete="email"
                style={{ background: 'rgba(255,255,255,0.1)', borderColor: 'rgba(255,255,255,0.2)', color: '#fff' }}
              />
            </Form.Item>

            <Form.Item
              name="password"
              label={<span style={{ color: 'rgba(255,255,255,0.85)', fontWeight: 600 }}>Mot de passe</span>}
              rules={[{ required: true, message: 'Mot de passe requis' }]}
              style={{ marginBottom: 28 }}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: '#bbb' }} />}
                placeholder="••••••••"
                autoComplete="current-password"
                style={{ background: 'rgba(255,255,255,0.1)', borderColor: 'rgba(255,255,255,0.2)', color: '#fff' }}
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                style={{
                  background: '#F9A825',
                  borderColor: 'transparent',
                  color: '#0D3B12',
                  height: 46,
                  fontSize: 15,
                  fontWeight: 700,
                  borderRadius: 8,
                }}
              >
                Se connecter
              </Button>
            </Form.Item>
          </Form>

          <Text style={{ color: 'rgba(255,255,255,0.3)', fontSize: 11, display: 'block', textAlign: 'center', marginTop: 40 }}>
            © NMA 2026
          </Text>
        </div>
      </div>
    </div>
  )
}
