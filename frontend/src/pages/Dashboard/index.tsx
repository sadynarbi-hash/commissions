import { useEffect, useState } from 'react'
import { Card, Col, Row, Statistic, Progress, Table, Typography, DatePicker, Spin, Tag, Empty } from 'antd'
import {
  TeamOutlined, TrophyOutlined, DollarOutlined,
  RiseOutlined, PercentageOutlined,
} from '@ant-design/icons'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, Cell,
} from 'recharts'
import dayjs from 'dayjs'
import { getDashboard, getEmployees } from '../../api/client'
import type { Employee } from '../../types'
import { TYPE_POSTE_LABELS } from '../../types'

const { Title } = Typography

// ─── Couleurs NMA ────────────────────────────────────────────────────────────
const NMA_GREEN  = '#1B5E20'
const NMA_GOLD   = '#F9A825'
const NMA_ORANGE = '#E65100'
const NMA_RED    = '#C62828'

const GAMME_COLORS: Record<string, string> = {
  FARINE:            '#F59E0B',
  PATES:             '#10B981',
  BETAIL:            '#8B4513',
  VOLAILLE:          '#F97316',
  BVF:               '#DC2626',
  NUTRITION_ANIMALE: '#8B5CF6',
  AUTRES:            '#6B7280',
}

// ─── Types ───────────────────────────────────────────────────────────────────
interface ZoneData   { zone: string; realise: number; objectif: number }
interface GammeData  { gamme: string; tonnage: number }
interface DashData {
  kpis: {
    nb_employes: number; nb_calcules: number; total_primes_fcfa: number
    taux_atteinte_moyen: number; ca_total_fcfa: number; taux_recouvrement: number
  }
  top_performers: Array<{ employee_id: number; taux_atteinte: number; total_prime: number }>
  by_role: Record<string, { count: number; total_prime: number; taux_moyen: number }>
  by_zone: ZoneData[]
  by_gamme: GammeData[]
}

const fmt = (v: number) => new Intl.NumberFormat('fr-FR').format(Math.round(v))
const fmtT = (v: number) => `${v.toFixed(1)} T`

// ─── Tooltip personnalisé ─────────────────────────────────────────────────
const ZoneTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  const realise  = payload.find((p: any) => p.dataKey === 'realise')?.value ?? 0
  const objectif = payload.find((p: any) => p.dataKey === 'objectif')?.value ?? 0
  const taux     = objectif > 0 ? (realise / objectif * 100) : 0
  return (
    <div style={{ background: '#fff', border: '1px solid #e8e8e8', borderRadius: 6, padding: '10px 14px', fontSize: 13 }}>
      <div style={{ fontWeight: 700, marginBottom: 6, color: '#333' }}>{label}</div>
      <div style={{ color: NMA_GREEN }}>Réalisé : <strong>{fmtT(realise)}</strong></div>
      <div style={{ color: NMA_GOLD }}>Objectif : <strong>{fmtT(objectif)}</strong></div>
      <div style={{ color: taux >= 100 ? NMA_GREEN : taux >= 90 ? '#fa8c16' : NMA_RED, marginTop: 4 }}>
        Atteinte : <strong>{taux.toFixed(1)} %</strong>
      </div>
    </div>
  )
}

const GammeTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#fff', border: '1px solid #e8e8e8', borderRadius: 6, padding: '10px 14px', fontSize: 13 }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{label}</div>
      <div>{fmtT(payload[0]?.value ?? 0)}</div>
    </div>
  )
}

// ─── Composant ───────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [periode, setPeriode] = useState(dayjs().format('YYYY-MM'))
  const [data, setData]       = useState<DashData | null>(null)
  const [employees, setEmployees] = useState<Employee[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    Promise.all([getDashboard(periode), getEmployees()])
      .then(([d, emps]) => { setData(d); setEmployees(emps) })
      .finally(() => setLoading(false))
  }, [periode])

  const empById = Object.fromEntries(employees.map(e => [e.id, e]))

  const topColumns = [
    {
      title: 'Commercial',
      dataIndex: 'employee_id',
      render: (id: number) => {
        const e = empById[id]
        return e ? `${e.prenom} ${e.nom}` : id
      },
    },
    {
      title: 'Rôle',
      dataIndex: 'employee_id',
      render: (id: number) => {
        const e = empById[id]
        return e ? <Tag>{TYPE_POSTE_LABELS[e.type_poste]}</Tag> : '-'
      },
    },
    {
      title: 'Taux atteinte',
      dataIndex: 'taux_atteinte',
      render: (v: number) => (
        <Progress
          percent={Math.min(v, 115)}
          size="small"
          status={v >= 100 ? 'success' : v >= 90 ? 'normal' : 'exception'}
          format={() => `${v?.toFixed(1)}%`}
        />
      ),
      sorter: (a: any, b: any) => a.taux_atteinte - b.taux_atteinte,
      defaultSortOrder: 'descend' as const,
    },
    {
      title: 'Commission totale',
      dataIndex: 'total_prime',
      render: (v: number) => fmt(v) + ' F',
    },
  ]

  const roleData = data
    ? Object.entries(data.by_role).map(([role, info]) => ({
        role: TYPE_POSTE_LABELS[role as keyof typeof TYPE_POSTE_LABELS] || role,
        ...info,
      }))
    : []

  return (
    <Spin spinning={loading}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0 }}>Tableau de bord</Title>
        <DatePicker
          picker="month"
          value={dayjs(periode)}
          format="MMMM YYYY"
          onChange={d => d && setPeriode(d.format('YYYY-MM'))}
        />
      </div>

      {data && (
        <>
          {/* ── KPI cards ── */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Total Commissions"
                  value={data.kpis.total_primes_fcfa}
                  formatter={v => fmt(Number(v)) + ' F'}
                  prefix={<TrophyOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Taux atteinte moyen"
                  value={data.kpis.taux_atteinte_moyen}
                  suffix="%"
                  prefix={<PercentageOutlined />}
                  valueStyle={{ color: data.kpis.taux_atteinte_moyen >= 90 ? '#52c41a' : '#fa8c16' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="CA Total période"
                  value={data.kpis.ca_total_fcfa}
                  formatter={v => fmt(Number(v)) + ' F'}
                  prefix={<DollarOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Taux recouvrement"
                  value={data.kpis.taux_recouvrement}
                  suffix="%"
                  prefix={<RiseOutlined />}
                  valueStyle={{ color: data.kpis.taux_recouvrement >= 90 ? '#52c41a' : '#ff4d4f' }}
                />
              </Card>
            </Col>
          </Row>

          {/* ── Graphiques ── */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            {/* Ventes vs Objectifs par zone */}
            <Col xs={24} lg={14}>
              <Card title="Ventes vs Objectifs par zone (tonnes)">
                {data.by_zone.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={data.by_zone} margin={{ top: 8, right: 16, left: 0, bottom: 0 }} barGap={4}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="zone" tick={{ fontSize: 13, fontWeight: 600 }} />
                      <YAxis tickFormatter={v => `${v}T`} tick={{ fontSize: 11 }} />
                      <Tooltip content={<ZoneTooltip />} />
                      <Legend
                        formatter={(value) => value === 'realise' ? 'Réalisé' : 'Objectif'}
                        wrapperStyle={{ fontSize: 13 }}
                      />
                      <Bar dataKey="realise" name="realise" fill={NMA_GREEN} radius={[4, 4, 0, 0]} maxBarSize={48} />
                      <Bar dataKey="objectif" name="objectif" fill={NMA_GOLD} radius={[4, 4, 0, 0]} maxBarSize={48} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <Empty description="Aucune donnée pour cette période" />
                )}
              </Card>
            </Col>

            {/* Ventes par gamme */}
            <Col xs={24} lg={10}>
              <Card title="Ventes par gamme (tonnes)">
                {data.by_gamme.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart
                      data={data.by_gamme}
                      layout="vertical"
                      margin={{ top: 8, right: 24, left: 16, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                      <XAxis type="number" tickFormatter={v => `${v}T`} tick={{ fontSize: 11 }} />
                      <YAxis type="category" dataKey="gamme" tick={{ fontSize: 12, fontWeight: 600 }} width={80} />
                      <Tooltip content={<GammeTooltip />} />
                      <Bar dataKey="tonnage" radius={[0, 4, 4, 0]} maxBarSize={32}>
                        {data.by_gamme.map(entry => (
                          <Cell
                            key={entry.gamme}
                            fill={GAMME_COLORS[entry.gamme] ?? NMA_ORANGE}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <Empty description="Aucune donnée pour cette période" />
                )}
              </Card>
            </Col>
          </Row>

          {/* ── Tableaux ── */}
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={16}>
              <Card title="Top Performers — Taux d'atteinte objectifs">
                <Table
                  dataSource={data.top_performers}
                  columns={topColumns}
                  rowKey="employee_id"
                  size="small"
                  pagination={false}
                />
              </Card>
            </Col>
            <Col xs={24} lg={8}>
              <Card title="Résultats par rôle">
                <Table
                  dataSource={roleData}
                  columns={[
                    { title: 'Rôle', dataIndex: 'role', ellipsis: true },
                    { title: 'Nb', dataIndex: 'count', width: 45 },
                    {
                      title: 'Taux moy.',
                      dataIndex: 'taux_moyen',
                      render: (v: number) => `${v.toFixed(1)}%`,
                    },
                  ]}
                  rowKey="role"
                  size="small"
                  pagination={false}
                />
              </Card>
            </Col>
          </Row>
        </>
      )}
    </Spin>
  )
}
