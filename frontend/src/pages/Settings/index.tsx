import { useEffect, useState } from 'react'
import {
  Card, Col, Row, Form, Input, Select, Button, Typography,
  Divider, Alert, Tabs, Table, Tag, Space, Modal, Popconfirm,
  message, Badge,
} from 'antd'
import {
  PlusOutlined, EditOutlined, KeyOutlined,
  StopOutlined, CheckOutlined, UserOutlined,
} from '@ant-design/icons'
import api from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'

const { Title, Text } = Typography
const { Option } = Select

// ─── Types ─────────────────────────────────────────────────────────────────

interface AppUser {
  id: number
  email: string
  nom: string
  role: string
  actif: boolean
}

const ROLE_LABELS: Record<string, string> = {
  ADMIN:     'Administrateur',
  DIRECTEUR: 'Directeur',
  ADJOINT:   'Adjoint Directeur',
  LECTEUR:   'Lecture seule',
}

const ROLE_COLORS: Record<string, string> = {
  ADMIN:     'red',
  DIRECTEUR: 'geekblue',
  ADJOINT:   'purple',
  LECTEUR:   'default',
}

// ─── Onglet Utilisateurs ────────────────────────────────────────────────────

function UsersTab() {
  const { user: me } = useAuth()
  const [users, setUsers] = useState<AppUser[]>([])
  const [loading, setLoading] = useState(false)
  const [createModal, setCreateModal] = useState(false)
  const [editModal, setEditModal] = useState<AppUser | null>(null)
  const [resetModal, setResetModal] = useState<AppUser | null>(null)
  const [saving, setSaving] = useState(false)
  const [createForm] = Form.useForm()
  const [editForm] = Form.useForm()
  const [resetForm] = Form.useForm()

  const load = () => {
    setLoading(true)
    api.get('/auth/users').then(r => setUsers(r.data)).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const onCreate = async () => {
    const values = await createForm.validateFields()
    setSaving(true)
    try {
      await api.post('/auth/users', values)
      message.success('Compte créé')
      createForm.resetFields()
      setCreateModal(false)
      load()
    } catch (err: any) {
      message.error(err?.response?.data?.detail ?? 'Erreur')
    } finally {
      setSaving(false)
    }
  }

  const onEdit = async () => {
    const values = await editForm.validateFields()
    setSaving(true)
    try {
      await api.patch(`/auth/users/${editModal!.id}`, values)
      message.success('Compte mis à jour')
      setEditModal(null)
      load()
    } catch (err: any) {
      message.error(err?.response?.data?.detail ?? 'Erreur')
    } finally {
      setSaving(false)
    }
  }

  const onReset = async () => {
    const values = await resetForm.validateFields()
    setSaving(true)
    try {
      await api.post(`/auth/users/${resetModal!.id}/reset-password`, { new_password: values.new_password })
      message.success('Mot de passe réinitialisé')
      resetForm.resetFields()
      setResetModal(null)
    } catch (err: any) {
      message.error(err?.response?.data?.detail ?? 'Erreur')
    } finally {
      setSaving(false)
    }
  }

  const toggleActif = async (u: AppUser) => {
    try {
      await api.patch(`/auth/users/${u.id}`, { actif: !u.actif })
      message.success(u.actif ? 'Compte désactivé' : 'Compte réactivé')
      load()
    } catch (err: any) {
      message.error(err?.response?.data?.detail ?? 'Erreur')
    }
  }

  const columns = [
    {
      title: 'Nom',
      dataIndex: 'nom',
      render: (nom: string, u: AppUser) => (
        <Space>
          <UserOutlined style={{ color: '#888' }} />
          <span style={{ fontWeight: 500, opacity: u.actif ? 1 : 0.45 }}>{nom}</span>
          {u.id === me?.id && <Tag color="green" style={{ fontSize: 10 }}>moi</Tag>}
        </Space>
      ),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      render: (email: string, u: AppUser) => (
        <Text style={{ opacity: u.actif ? 1 : 0.45 }}>{email}</Text>
      ),
    },
    {
      title: 'Rôle',
      dataIndex: 'role',
      render: (role: string) => (
        <Tag color={ROLE_COLORS[role] ?? 'default'}>{ROLE_LABELS[role] ?? role}</Tag>
      ),
    },
    {
      title: 'Statut',
      dataIndex: 'actif',
      render: (actif: boolean) => (
        <Badge status={actif ? 'success' : 'default'} text={actif ? 'Actif' : 'Inactif'} />
      ),
    },
    {
      title: 'Actions',
      render: (_: unknown, u: AppUser) => (
        <Space size="small">
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => { setEditModal(u); editForm.setFieldsValue({ nom: u.nom, role: u.role }) }}
          >
            Modifier
          </Button>
          <Button
            size="small"
            icon={<KeyOutlined />}
            onClick={() => { setResetModal(u); resetForm.resetFields() }}
          >
            Mot de passe
          </Button>
          <Popconfirm
            title={u.actif ? 'Désactiver ce compte ?' : 'Réactiver ce compte ?'}
            onConfirm={() => toggleActif(u)}
            disabled={u.id === me?.id}
          >
            <Button
              size="small"
              danger={u.actif}
              icon={u.actif ? <StopOutlined /> : <CheckOutlined />}
              disabled={u.id === me?.id}
            >
              {u.actif ? 'Désactiver' : 'Réactiver'}
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Text type="secondary">{users.filter(u => u.actif).length} compte(s) actif(s)</Text>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setCreateModal(true); createForm.resetFields() }}>
          Nouveau compte
        </Button>
      </div>

      <Table
        dataSource={users}
        columns={columns}
        rowKey="id"
        loading={loading}
        size="small"
        pagination={false}
      />

      {/* Modal création */}
      <Modal
        title="Créer un compte"
        open={createModal}
        onOk={onCreate}
        onCancel={() => setCreateModal(false)}
        confirmLoading={saving}
        okText="Créer"
        cancelText="Annuler"
      >
        <Form form={createForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="nom" label="Nom complet" rules={[{ required: true, message: 'Requis' }]}>
            <Input placeholder="Prénom Nom" />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true }, { type: 'email', message: 'Email invalide' }]}>
            <Input placeholder="prenom.nom@nmasanders.com" />
          </Form.Item>
          <Form.Item name="password" label="Mot de passe" rules={[{ required: true }, { min: 6, message: '6 caractères minimum' }]}>
            <Input.Password placeholder="Minimum 6 caractères" />
          </Form.Item>
          <Form.Item name="role" label="Rôle" initialValue="LECTEUR" rules={[{ required: true }]}>
            <Select>
              {Object.entries(ROLE_LABELS).map(([val, label]) => (
                <Option key={val} value={val}>{label}</Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal modification */}
      <Modal
        title={`Modifier — ${editModal?.nom}`}
        open={!!editModal}
        onOk={onEdit}
        onCancel={() => setEditModal(null)}
        confirmLoading={saving}
        okText="Enregistrer"
        cancelText="Annuler"
      >
        <Form form={editForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="nom" label="Nom complet" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="role" label="Rôle" rules={[{ required: true }]}>
            <Select>
              {Object.entries(ROLE_LABELS).map(([val, label]) => (
                <Option key={val} value={val}>{label}</Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal reset password */}
      <Modal
        title={`Réinitialiser le mot de passe — ${resetModal?.nom}`}
        open={!!resetModal}
        onOk={onReset}
        onCancel={() => setResetModal(null)}
        confirmLoading={saving}
        okText="Réinitialiser"
        cancelText="Annuler"
      >
        <Form form={resetForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="new_password"
            label="Nouveau mot de passe"
            rules={[{ required: true }, { min: 6, message: '6 caractères minimum' }]}
          >
            <Input.Password placeholder="Minimum 6 caractères" />
          </Form.Item>
          <Form.Item
            name="confirm"
            label="Confirmer"
            dependencies={['new_password']}
            rules={[
              { required: true },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) return Promise.resolve()
                  return Promise.reject('Les mots de passe ne correspondent pas')
                },
              }),
            ]}
          >
            <Input.Password />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

// ─── Page principale ────────────────────────────────────────────────────────

export default function Settings() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'ADMIN'

  const tabItems = [
    ...(isAdmin ? [{
      key: 'users',
      label: 'Utilisateurs',
      children: (
        <Card>
          <UsersTab />
        </Card>
      ),
    }] : []),
    {
      key: 'connexions',
      label: 'Connexions',
      children: (
        <div>
          <Alert
            message="Les paramètres de connexion sont définis dans le fichier .env du backend."
            description="Modifiez backend/.env puis redémarrez le serveur."
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Card title="SAP Business One">
                <Form layout="vertical">
                  <Form.Item label="Type"><Select defaultValue="sqlserver" disabled><Option value="sqlserver">SQL Server</Option></Select></Form.Item>
                  <Form.Item label="Serveur"><Input placeholder="SAP_SERVER (défini dans .env)" disabled /></Form.Item>
                  <Form.Item label="Base de données"><Input placeholder="SAP_DATABASE (défini dans .env)" disabled /></Form.Item>
                  <Form.Item label="Utilisateur"><Input placeholder="SAP_USERNAME (défini dans .env)" disabled /></Form.Item>
                  <Divider />
                  <p style={{ fontSize: 12, color: '#888' }}>Tables : <code>ODLN</code>, <code>DLN1</code>, <code>OINV</code>, <code>OCRD</code>, <code>@COMSECTEURLIGNE</code></p>
                </Form>
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <Card title="Salesforce">
                <Form layout="vertical">
                  <Form.Item label="Utilisateur"><Input placeholder="SF_USERNAME (défini dans .env)" disabled /></Form.Item>
                  <Form.Item label="Domaine"><Select defaultValue="login" disabled><Option value="login">Production</Option><Option value="test">Sandbox</Option></Select></Form.Item>
                  <Divider />
                  <p style={{ fontSize: 12, color: '#888' }}>Objets : <code>Task</code> (visites, rapports, planning)</p>
                </Form>
              </Card>
            </Col>
          </Row>
          <Card title="Base de données locale (PostgreSQL)" style={{ marginTop: 16 }}>
            <p style={{ color: '#888' }}>Connexion via <code>DATABASE_URL</code> dans <code>.env</code>. Tables créées automatiquement au démarrage.</p>
          </Card>
        </div>
      ),
    },
  ]

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>Paramètres</Title>
      <Tabs defaultActiveKey={isAdmin ? 'users' : 'connexions'} items={tabItems} />
    </div>
  )
}
