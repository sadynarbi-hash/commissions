import { useEffect, useState } from 'react'
import {
  Table, DatePicker, Button, Tag, Space, Progress, Typography,
  Drawer, Descriptions, Divider, message, Modal, Input,
  Badge, Select, Card, Statistic, Row, Col, Switch,
} from 'antd'
import {
  CalculatorOutlined, CheckCircleOutlined,
  DownloadOutlined, EyeOutlined, FilePdfOutlined,
  TrophyOutlined, TeamOutlined, WalletOutlined, RiseOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import {
  getBonuses, calculateBonuses, validateBonuses,
  getEmployees, exportBonuses, downloadPV, downloadRecap,
} from '../../api/client'
import type { Bonus, Employee } from '../../types'
import { TYPE_POSTE_LABELS } from '../../types'

const { Title } = Typography

const STATUT_COLORS: Record<string, string> = {
  BROUILLON: 'default',
  CALCULE: 'processing',
  EN_VALIDATION: 'warning',
  VALIDE: 'success',
  PAYE: 'green',
}

const formatFCFA = (v: number) => new Intl.NumberFormat('fr-FR').format(Math.round(v)) + ' F'

const rowBg = (taux?: number | null, hasObj?: boolean) => {
  if (!hasObj || taux == null) return {}
  if (taux >= 115) return { style: { background: '#e6f4ea' } }
  if (taux >= 100) return { style: { background: '#f0faf0' } }
  if (taux >= 90)  return { style: { background: '#fff8e6' } }
  return { style: { background: '#fff1f0' } }
}

export default function Bonuses() {
  const [periode, setPeriode] = useState(dayjs().format('YYYY-MM'))
  const [bonuses, setBonuses] = useState<Bonus[]>([])
  const [employees, setEmployees] = useState<Employee[]>([])
  const [loading, setLoading] = useState(false)
  const [calculating, setCalculating] = useState(false)
  const [selected, setSelected] = useState<Bonus | null>(null)
  const [validateModal, setValidateModal] = useState(false)
  const [validateurNom, setValidateurNom] = useState('')
  const [roleFilter, setRoleFilter] = useState<string | null>(null)
  const [hideZeros, setHideZeros] = useState(false)

  const load = () => {
    setLoading(true)
    Promise.all([getBonuses({ periode }), getEmployees()])
      .then(([bs, emps]) => {
        setBonuses(bs)
        setEmployees(emps)
        setSelected(prev => prev ? (bs.find((b: Bonus) => b.id === prev.id) ?? prev) : null)
      })
      .finally(() => setLoading(false))
  }

  useEffect(load, [periode])

  const empById = Object.fromEntries(employees.map(e => [e.id, e]))

  const onCalculate = async () => {
    setCalculating(true)
    try {
      const result = await calculateBonuses(periode)
      message.success(`${result.nb_calcules} primes calculées`)
      load()
    } catch {
      message.error('Erreur lors du calcul')
    } finally {
      setCalculating(false)
    }
  }

  const onValidate = async () => {
    if (!validateurNom.trim()) return
    await validateBonuses(periode, validateurNom)
    message.success('Primes validées')
    setValidateModal(false)
    load()
  }

  const onExport = async () => {
    const resp = await exportBonuses(periode)
    const url = URL.createObjectURL(resp.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `primes_${periode}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  }

  const columns = [
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
        return e ? <Tag color="blue">{e.type_poste}</Tag> : '-'
      },
    },
    {
      title: 'Réalisé (T)',
      dataIndex: 'volume_realise',
      render: (v: number) => v > 0 ? new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 1 }).format(v) : '—',
      sorter: (a: Bonus, b: Bonus) => (a.volume_realise || 0) - (b.volume_realise || 0),
    },
    {
      title: 'Objectif (T)',
      dataIndex: 'volume_objectif',
      render: (v: number) => v > 0 ? new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 1 }).format(v) : '—',
    },
    {
      title: 'Taux atteinte',
      dataIndex: 'taux_atteinte_global',
      render: (v?: number) => v != null ? (
        <Progress
          percent={Math.min(v, 115)}
          size="small"
          status={v >= 100 ? 'success' : v >= 90 ? 'normal' : 'exception'}
          format={() => `${v.toFixed(1)}%`}
        />
      ) : '—',
      sorter: (a: Bonus, b: Bonus) => (a.taux_atteinte_global || 0) - (b.taux_atteinte_global || 0),
    },
    {
      title: 'Visites',
      dataIndex: 'nb_visites',
      render: (v: number) => v > 0 ? v : '—',
      sorter: (a: Bonus, b: Bonus) => (a.nb_visites || 0) - (b.nb_visites || 0),
    },
    {
      title: 'Prime fixe',
      dataIndex: 'prime_suivi_fixe',
      render: (v: number) => v > 0
        ? <span style={{ color: '#555' }}>{formatFCFA(v)}</span>
        : <span style={{ color: '#ccc' }}>—</span>,
    },
    {
      title: 'Prime quant.',
      dataIndex: 'prime_quantitative',
      render: (v: number) => v > 0
        ? <span style={{ color: '#1B5E20', fontWeight: 600 }}>{formatFCFA(v)}</span>
        : <span style={{ color: '#ccc' }}>0 F</span>,
      sorter: (a: Bonus, b: Bonus) => (a.prime_quantitative || 0) - (b.prime_quantitative || 0),
    },
    {
      title: 'Prime qual.',
      dataIndex: 'prime_qualitative',
      render: (v: number) => v > 0
        ? <span style={{ color: '#52c41a', fontWeight: 600 }}>{formatFCFA(v)}</span>
        : <span style={{ color: '#ccc' }}>0 F</span>,
      sorter: (a: Bonus, b: Bonus) => (a.prime_qualitative || 0) - (b.prime_qualitative || 0),
    },
    {
      title: 'TOTAL',
      dataIndex: 'total',
      width: 120,
      render: (v: number) => <strong style={{ color: '#1890ff', whiteSpace: 'nowrap' }}>{formatFCFA(v)}</strong>,
      sorter: (a: Bonus, b: Bonus) => a.total - b.total,
    },
    {
      title: 'Statut',
      dataIndex: 'statut',
      render: (v: string) => <Badge status={STATUT_COLORS[v] as any} text={v} />,
    },
    {
      title: '',
      render: (_: unknown, r: Bonus) => (
        <Space size={4}>
          <Button size="small" icon={<EyeOutlined />} onClick={() => setSelected(r)}>
            Détail
          </Button>
          <Button
            size="small"
            icon={<FilePdfOutlined />}
            style={{ borderColor: '#E65100', color: '#E65100' }}
            onClick={async () => {
              try {
                const resp = await downloadPV(r.id)
                const url = URL.createObjectURL(resp.data)
                const a = document.createElement('a')
                const emp = empById[r.employee_id]
                a.href = url
                a.download = `PV_${emp ? emp.nom + '_' + emp.prenom : r.id}_${periode}.pdf`
                a.click()
                URL.revokeObjectURL(url)
              } catch (err: any) {
                const detail = err?.response?.data
                if (detail instanceof Blob) {
                  const text = await detail.text()
                  try { message.error(JSON.parse(text).detail?.substring(0, 200)) }
                  catch { message.error(text.substring(0, 200)) }
                } else {
                  message.error(String(err?.message || 'Erreur génération PDF'))
                }
              }
            }}
          >
            PV
          </Button>
        </Space>
      ),
    },
  ]

  const bonusesFiltered = bonuses
    .filter(b => roleFilter ? empById[b.employee_id]?.type_poste === roleFilter : true)
    .filter(b => hideZeros ? b.total > 0 : true)

  const total         = bonusesFiltered.reduce((s, b) => s + b.total, 0)
  const nbAvecObj     = bonusesFiltered.filter(b => (b.volume_objectif || 0) > 0).length
  const nb100         = bonusesFiltered.filter(b => (b.taux_atteinte_global || 0) >= 100).length
  const totalQual     = bonusesFiltered.reduce((s, b) => s + (b.prime_qualitative || 0), 0)

  return (
    <div style={{ padding: 24, background: '#f4f6f0', minHeight: '100%' }}>

      {/* ── Barre d'actions ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <span style={{ fontSize: 14, color: '#1B5E20', fontWeight: 600 }}>
          Commissions — {dayjs(periode).format('MMMM YYYY')}
        </span>
        <Space wrap>
          <DatePicker
            picker="month"
            value={dayjs(periode)}
            format="MMMM YYYY"
            onChange={d => d && setPeriode(d.format('YYYY-MM'))}
          />
          <Select
            allowClear
            placeholder="Tous les rôles"
            style={{ width: 180 }}
            value={roleFilter}
            onChange={v => setRoleFilter(v ?? null)}
            options={[
              { value: 'COMMERCIAL',   label: 'Commercial' },
              { value: 'RCR',          label: 'Resp. Commercial Régional' },
              { value: 'SV',           label: 'Superviseur des Ventes' },
              { value: 'ATC_BV',       label: 'ATC Bétail & Volaille' },
              { value: 'ATC_FARINE',   label: 'ATC Farine' },
              { value: 'DCMT',         label: 'DCMT' },
              { value: 'DV',           label: 'Directeur des Ventes' },
            ]}
          />
          <Space size={6}>
            <Switch size="small" checked={hideZeros} onChange={setHideZeros} />
            <span style={{ fontSize: 13, color: '#666' }}>Masquer les 0</span>
          </Space>
          <Button icon={<CalculatorOutlined />} loading={calculating} onClick={onCalculate} type="primary">
            Calculer
          </Button>
          <Button icon={<CheckCircleOutlined />} onClick={() => setValidateModal(true)} disabled={bonuses.length === 0}>
            Valider
          </Button>
          <Button icon={<DownloadOutlined />} onClick={onExport} disabled={bonuses.length === 0}>
            Excel
          </Button>
          <Button
            icon={<FilePdfOutlined />}
            style={{ borderColor: '#1B5E20', color: '#1B5E20' }}
            disabled={bonuses.length === 0}
            onClick={async () => {
              try {
                const resp = await downloadRecap(periode)
                const url = URL.createObjectURL(resp.data)
                const a = document.createElement('a')
                a.href = url
                a.download = `recap_commissions_${periode}.pdf`
                a.click()
                URL.revokeObjectURL(url)
              } catch {
                message.error('Erreur génération récapitulatif')
              }
            }}
          >
            Récap RH
          </Button>
        </Space>
      </div>

      {/* ── Cartes de synthèse ── */}
      <Row gutter={16} style={{ marginBottom: 20 }}>
        <Col span={6}>
          <Card bordered={false} style={{ borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
            <Statistic
              title="Masse salariale"
              value={total}
              suffix="F"
              formatter={v => new Intl.NumberFormat('fr-FR').format(Number(v))}
              valueStyle={{ color: '#1890ff', fontWeight: 700 }}
              prefix={<WalletOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} style={{ borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
            <Statistic
              title="Commerciaux avec objectif"
              value={nbAvecObj}
              suffix={`/ ${bonusesFiltered.length}`}
              valueStyle={{ color: '#555' }}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} style={{ borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
            <Statistic
              title="Objectif atteint (≥ 100%)"
              value={nb100}
              suffix={`/ ${nbAvecObj}`}
              valueStyle={{ color: '#1B5E20', fontWeight: 700 }}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} style={{ borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
            <Statistic
              title="Total primes qualitatives"
              value={totalQual}
              suffix="F"
              formatter={v => new Intl.NumberFormat('fr-FR').format(Number(v))}
              valueStyle={{ color: '#52c41a', fontWeight: 700 }}
              prefix={<RiseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* ── Tableau ── */}
      <div style={{ background: '#fff', borderRadius: 8, padding: '0 0 8px', boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
        <Table
          dataSource={bonusesFiltered}
          columns={columns}
          rowKey="id"
          loading={loading}
          size="small"
          onRow={(record: Bonus) => rowBg(record.taux_atteinte_global, (record.volume_objectif || 0) > 0)}
          summary={() => (
            <Table.Summary.Row style={{ background: '#fafafa' }}>
              <Table.Summary.Cell index={0} colSpan={9}>
                <span style={{ fontSize: 12, color: '#888' }}>Total général</span>
              </Table.Summary.Cell>
              <Table.Summary.Cell index={9} style={{ whiteSpace: 'nowrap', minWidth: 120 }}>
                <span style={{ fontSize: 12, color: '#1890ff', fontWeight: 600 }}>{formatFCFA(total)}</span>
              </Table.Summary.Cell>
              <Table.Summary.Cell index={10} colSpan={2} />
            </Table.Summary.Row>
          )}
        />
      </div>

      {/* ── Drawer détail ── */}
      <Drawer
        title="Détail de la commission"
        open={!!selected}
        onClose={() => setSelected(null)}
        width={520}
      >
        {selected && (() => {
          const emp = empById[selected.employee_id]
          return (
            <>
              <Descriptions column={1} size="small" bordered>
                <Descriptions.Item label="Commercial">
                  {emp ? `${emp.prenom} ${emp.nom}` : selected.employee_id}
                </Descriptions.Item>
                <Descriptions.Item label="Rôle">
                  {emp ? TYPE_POSTE_LABELS[emp.type_poste] : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="Taux atteinte global">
                  {selected.taux_atteinte_global?.toFixed(1)}%
                </Descriptions.Item>
                {selected.taux_atteinte_pates != null && (
                  <Descriptions.Item label="Taux Pâtes">
                    {selected.taux_atteinte_pates.toFixed(1)}%
                  </Descriptions.Item>
                )}
                {selected.taux_atteinte_autres != null && (
                  <Descriptions.Item label="Taux Autres gammes">
                    {selected.taux_atteinte_autres.toFixed(1)}%
                  </Descriptions.Item>
                )}
                <Descriptions.Item label="Commission fixe">
                  {formatFCFA(selected.prime_suivi_fixe)}
                </Descriptions.Item>
                <Descriptions.Item label="Commission quantitative">
                  <span style={{ color: selected.prime_quantitative > 0 ? '#1B5E20' : '#aaa', fontWeight: 600 }}>
                    {formatFCFA(selected.prime_quantitative)}
                  </span>
                </Descriptions.Item>
                <Descriptions.Item label="Commission qualitative">
                  <span style={{ color: selected.prime_qualitative > 0 ? '#52c41a' : '#aaa', fontWeight: 600 }}>
                    {formatFCFA(selected.prime_qualitative)}
                  </span>
                </Descriptions.Item>
                {selected.commission_nouvelles_affaires != null && (
                  <Descriptions.Item label="Commission nouvelles affaires (0.5%)">
                    <span style={{ color: selected.commission_nouvelles_affaires > 0 ? '#1890ff' : '#aaa' }}>
                      {formatFCFA(selected.commission_nouvelles_affaires)}
                    </span>
                  </Descriptions.Item>
                )}
                <Descriptions.Item label="Qualitative éligible">
                  <Tag color={selected.qualitative_eligible ? 'green' : 'red'}>
                    {selected.qualitative_eligible ? 'OUI (≥90%)' : 'NON (<90%)'}
                  </Tag>
                </Descriptions.Item>
              </Descriptions>

              <Divider>Critères commission qualitative</Divider>
              {selected.qual_details.map(c => (
                <div
                  key={c.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '6px 0',
                    borderBottom: '1px solid #f0f0f0',
                    opacity: selected.qualitative_eligible ? 1 : 0.5,
                  }}
                >
                  <div>
                    <Tag color={c.eligible ? 'green' : 'red'} style={{ marginRight: 8 }}>
                      {c.eligible ? '✓' : '✗'}
                    </Tag>
                    <span style={{ fontSize: 13 }}>{c.critere_libelle}</span>
                    {c.valeur_atteinte && (
                      <span style={{ color: '#888', marginLeft: 8, fontSize: 12 }}>
                        ({c.valeur_atteinte} / {c.seuil_requis})
                      </span>
                    )}
                  </div>
                  <strong style={{ color: c.eligible ? '#52c41a' : '#aaa', minWidth: 80, textAlign: 'right' }}>
                    {formatFCFA(c.montant_accorde)} / {formatFCFA(c.montant_max)}
                  </strong>
                </div>
              ))}

              <Divider />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 16 }}>
                <strong>TOTAL COMMISSION</strong>
                <strong style={{ color: '#1890ff' }}>{formatFCFA(selected.total)}</strong>
              </div>
            </>
          )
        })()}
      </Drawer>

      <Modal
        title="Valider les commissions"
        open={validateModal}
        onOk={onValidate}
        onCancel={() => setValidateModal(false)}
        okText="Valider"
      >
        <p>Saisir votre nom pour valider les commissions de <strong>{periode}</strong> :</p>
        <Input
          value={validateurNom}
          onChange={e => setValidateurNom(e.target.value)}
          placeholder="Nom du validateur"
        />
      </Modal>
    </div>
  )
}
