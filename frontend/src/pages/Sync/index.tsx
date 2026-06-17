import { useEffect, useState } from 'react'
import {
  Card, Col, Row, Button, DatePicker, Table, Tag,
  Typography, Space, message, Alert,
} from 'antd'
import {
  SyncOutlined, ApiOutlined, CheckCircleOutlined, CloseCircleOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { triggerSync, getSyncLogs, testConnection } from '../../api/client'
import type { SyncLog } from '../../types'

const { Title } = Typography

const STATUT_CONFIG = {
  EN_COURS: { color: 'processing', label: 'En cours' },
  SUCCES: { color: 'success', label: 'Succès' },
  ERREUR: { color: 'error', label: 'Erreur' },
}

export default function Sync() {
  const [periode, setPeriode] = useState(dayjs().format('YYYY-MM'))
  const [logs, setLogs] = useState<SyncLog[]>([])
  const [loading, setLoading] = useState(false)
  const [sapStatus, setSapStatus] = useState<boolean | null>(null)
  const [sfStatus, setSfStatus] = useState<boolean | null>(null)
  const [syncing, setSyncing] = useState<string | null>(null)

  const loadLogs = () => {
    setLoading(true)
    getSyncLogs().then(setLogs).finally(() => setLoading(false))
  }

  useEffect(loadLogs, [])

  const handleSync = async (source: 'SAP' | 'SALESFORCE') => {
    setSyncing(source)
    try {
      await triggerSync(source, periode)
      message.success(`Synchronisation ${source} lancée pour ${periode}`)
      setTimeout(loadLogs, 2000)
    } catch {
      message.error('Erreur lors du lancement de la synchronisation')
    } finally {
      setSyncing(null)
    }
  }

  const handleTestSAP = async () => {
    const r = await testConnection('SAP')
    setSapStatus(r.ok)
    message.info(r.message)
  }

  const handleTestSF = async () => {
    const r = await testConnection('SALESFORCE')
    setSfStatus(r.ok)
    message.info(r.message)
  }

  const columns = [
    {
      title: 'Source',
      dataIndex: 'source',
      render: (v: string) => <Tag color={v === 'SAP' ? 'blue' : 'green'}>{v}</Tag>,
    },
    { title: 'Période', dataIndex: 'periode', render: (v?: string) => v || '—' },
    {
      title: 'Statut',
      dataIndex: 'statut',
      render: (v: string) => {
        const cfg = STATUT_CONFIG[v as keyof typeof STATUT_CONFIG]
        return <Tag color={cfg?.color}>{cfg?.label || v}</Tag>
      },
    },
    {
      title: 'Enregistrements',
      dataIndex: 'nb_records',
      render: (v: number) => v.toLocaleString('fr-FR'),
    },
    {
      title: 'Démarré',
      dataIndex: 'started_at',
      render: (v: string) => dayjs(v).format('DD/MM/YYYY HH:mm'),
    },
    {
      title: 'Terminé',
      dataIndex: 'ended_at',
      render: (v?: string) => v ? dayjs(v).format('HH:mm:ss') : '—',
    },
    {
      title: 'Message',
      dataIndex: 'message',
      ellipsis: true,
      render: (v?: string) => v ? <span style={{ color: '#ff4d4f', fontSize: 12 }}>{v}</span> : '—',
    },
  ]

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>Synchronisation des données</Title>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        {/* SAP B1 */}
        <Col xs={24} md={12}>
          <Card
            title={<><ApiOutlined /> SAP Business One</>}
            extra={
              sapStatus !== null && (
                sapStatus
                  ? <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
              )
            }
          >
            <Alert
              message="Synchronise les ventes et le recouvrement"
              description="Factures (OINV), Encaissements (ORCT), Portefeuille clients (OCRD)"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Space direction="vertical" style={{ width: '100%' }}>
              <DatePicker
                picker="month"
                value={dayjs(periode)}
                format="MMMM YYYY"
                onChange={d => d && setPeriode(d.format('YYYY-MM'))}
                style={{ width: '100%' }}
              />
              <Space>
                <Button onClick={handleTestSAP}>Tester connexion</Button>
                <Button
                  type="primary"
                  icon={<SyncOutlined />}
                  loading={syncing === 'SAP'}
                  onClick={() => handleSync('SAP')}
                >
                  Synchroniser SAP
                </Button>
              </Space>
            </Space>
          </Card>
        </Col>

        {/* Salesforce */}
        <Col xs={24} md={12}>
          <Card
            title={<><ApiOutlined /> Salesforce</>}
            extra={
              sfStatus !== null && (
                sfStatus
                  ? <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
              )
            }
          >
            <Alert
              message="Synchronise les visites et la conformité CRM"
              description="Activités (Task), Visites fermes, Rapports, Planning commerciaux"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Space direction="vertical" style={{ width: '100%' }}>
              <DatePicker
                picker="month"
                value={dayjs(periode)}
                format="MMMM YYYY"
                onChange={d => d && setPeriode(d.format('YYYY-MM'))}
                style={{ width: '100%' }}
              />
              <Space>
                <Button onClick={handleTestSF}>Tester connexion</Button>
                <Button
                  type="primary"
                  icon={<SyncOutlined />}
                  loading={syncing === 'SALESFORCE'}
                  onClick={() => handleSync('SALESFORCE')}
                >
                  Synchroniser Salesforce
                </Button>
              </Space>
            </Space>
          </Card>
        </Col>
      </Row>

      <Card title="Historique des synchronisations">
        <Table
          dataSource={logs}
          columns={columns}
          rowKey="id"
          loading={loading}
          size="small"
          pagination={{ pageSize: 20 }}
        />
      </Card>
    </div>
  )
}
