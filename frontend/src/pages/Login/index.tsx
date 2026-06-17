import { useState } from 'react'
import { Form, Input, Button, Card, Typography, Alert } from 'antd'
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
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0D3B12 0%, #1B5E20 60%, #2E7D32 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <Card
        style={{
          width: 400,
          borderRadius: 12,
          boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
          border: 'none',
        }}
        bodyStyle={{ padding: '40px 36px' }}
      >
        {/* Logo + titre */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <img
            src="/logo-nma.png"
            alt="NMA"
            style={{ height: 56, objectFit: 'contain', marginBottom: 12 }}
            onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
          <Title level={3} style={{ margin: 0, color: '#1B5E20' }}>
            Gestion des Commissions
          </Title>
          <Text style={{ color: '#888', fontSize: 13 }}>
            Nouvelle Minoterie Africaine
          </Text>
        </div>

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
            rules={[{ required: true, message: 'Email requis' }, { type: 'email', message: 'Email invalide' }]}
          >
            <Input
              prefix={<MailOutlined style={{ color: '#bbb' }} />}
              placeholder="Adresse e-mail"
              autoComplete="email"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Mot de passe requis' }]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: '#bbb' }} />}
              placeholder="Mot de passe"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{ background: '#1B5E20', borderColor: '#1B5E20', height: 44 }}
            >
              Se connecter
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
