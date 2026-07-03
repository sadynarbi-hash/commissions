import { useEffect, useState, useMemo, useRef } from 'react'
import {
  DatePicker, Button, Modal, Form, Select,
  InputNumber, Typography, Space, message, Tag, Alert, Spin,
} from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { getObjectives, upsertObjective, deleteObjective, getEmployees, getRegions } from '../../api/client'
import api from '../../api/client'
import type { Objective, Employee } from '../../types'
import { TYPE_POSTE_LABELS } from '../../types'

const { Title } = Typography
const { Option } = Select

const GAMMES = [
  { value: 'BETAIL',            label: 'Bétail',                color: '#6A1B9A' },
  { value: 'VOLAILLE',          label: 'Volaille',              color: '#00695C' },
  { value: 'BVF',               label: 'Bétail+Volaille',       color: '#4527A0' },
  { value: 'PATES',             label: 'Pâtes',                 color: '#1565C0' },
  { value: 'FARINE',            label: 'Farine',                color: '#E65100' },
  { value: 'NUTRITION_ANIMALE', label: 'Nutrition Animale',     color: '#558B2F' },
  { value: 'ALL',               label: 'Toutes gammes',         color: '#37474F' },
]
const GAMME_MAP = Object.fromEntries(GAMMES.map(g => [g.value, g]))

const ZONE_COLORS: Record<string, string> = {
  DAKAR: '#1565C0', NORD: '#6A1B9A', CENTRE: '#1B5E20', SUD: '#E65100', EXPORT: '#00695C',
}

const fmt = (n?: number | null) =>
  n != null ? new Intl.NumberFormat('fr-FR').format(Math.round(n)) : '—'

export default function Objectives() {
  const [periode, setPeriode]         = useState(dayjs().format('YYYY-MM'))
  const [zoneFilter, setZoneFilter]   = useState<number | undefined>()
  const [gammeFilter, setGammeFilter] = useState<string | undefined>()
  const [objectives, setObjectives]   = useState<Objective[]>([])
  const [employees, setEmployees]     = useState<Employee[]>([])
  const [regions, setRegions]         = useState<{ id: number; nom: string }[]>([])
  const [loading, setLoading]         = useState(false)
  const [modalOpen, setModalOpen]     = useState(false)
  const [editing, setEditing]         = useState<Objective | null>(null)
  const [form] = Form.useForm()

  const [importOpen, setImportOpen]   = useState(false)
  const [importLoading, setImportLoading] = useState(false)
  const [importFile, setImportFile]   = useState<File | null>(null)
  const [importResult, setImportResult] = useState<{
    created: number; updated: number; errors: {nom: string; raison: string}[]
  } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const load = () => {
    setLoading(true)
    Promise.all([getObjectives({ periode }), getEmployees(), getRegions()])
      .then(([objs, emps, regs]) => { setObjectives(objs); setEmployees(emps); setRegions(regs) })
      .finally(() => setLoading(false))
  }
  useEffect(load, [periode])

  const empById = useMemo(() => Object.fromEntries(employees.map(e => [e.id, e])), [employees])

  // ── filtres combinés ─────────────────────────────────────────────────────
  const filtered = useMemo(() => objectives.filter(o => {
    const emp = empById[o.employee_id]
    if (zoneFilter  && emp?.region_id !== zoneFilter)  return false
    if (gammeFilter && o.gamme        !== gammeFilter)  return false
    return true
  }), [objectives, empById, zoneFilter, gammeFilter])

  // ── totaux par gamme sur la sélection ────────────────────────────────────
  const totauxParGamme = useMemo(() => {
    const acc: Record<string, number> = {}
    filtered.forEach(o => {
      if (o.objectif_volume) acc[o.gamme] = (acc[o.gamme] ?? 0) + o.objectif_volume
    })
    return acc
  }, [filtered])

  const totalGeneral = useMemo(
    () => Object.values(totauxParGamme).reduce((s, v) => s + v, 0),
    [totauxParGamme]
  )

  // ── modal helpers ────────────────────────────────────────────────────────
  const openAdd = () => { setEditing(null); form.resetFields(); setModalOpen(true) }
  const openEdit = (obj: Objective) => {
    setEditing(obj)
    form.setFieldsValue({ employee_id: obj.employee_id, gamme: obj.gamme,
      objectif_volume: obj.objectif_volume, objectif_ca: obj.objectif_ca })
    setModalOpen(true)
  }
  const onSave = async () => {
    const values = await form.validateFields()
    try {
      await upsertObjective({ ...values, periode })
      message.success('Objectif sauvegardé')
      setModalOpen(false); load()
    } catch { message.error('Erreur lors de la sauvegarde') }
  }
  const onDelete = async (id: number) => {
    await deleteObjective(id); message.success('Supprimé'); load()
  }

  const downloadTemplate = () => {
    const a = document.createElement('a')
    a.href = '/api/objectives/template'
    a.download = 'objectifs_template.xlsx'
    a.click()
  }

  const openImport = () => {
    setImportFile(null)
    setImportResult(null)
    setImportOpen(true)
  }

  const onImport = async () => {
    if (!importFile) return
    setImportLoading(true)
    try {
      const fd = new FormData()
      fd.append('file', importFile)
      fd.append('periode', periode)
      const res = await api.post('/objectives/import', fd)
      setImportResult(res.data)
      if (res.data.created + res.data.updated > 0) load()
    } catch (e: any) {
      message.error(e?.response?.data?.detail ?? "Erreur lors de l'import")
    } finally {
      setImportLoading(false)
    }
  }

  const zoneName = regions.find(r => r.id === zoneFilter)?.nom
  const selectionLabel = [zoneName, GAMME_MAP[gammeFilter ?? '']?.label].filter(Boolean).join(' · ') || 'Tout'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* ── Barre filtres ── */}
      <div style={{
        background: '#fff', borderRadius: 10, padding: '14px 20px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.07)',
        display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
      }}>
        <Title level={5} style={{ margin: 0, color: '#1B5E20', flexShrink: 0 }}>Objectifs</Title>
        <div style={{ flex: 1, display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <DatePicker
            picker="month" value={dayjs(periode)} format="MMMM YYYY"
            onChange={d => d && setPeriode(d.format('YYYY-MM'))}
          />
          <Select
            placeholder="Toutes les zones" allowClear style={{ width: 150 }}
            value={zoneFilter} onChange={v => setZoneFilter(v)}
          >
            {regions.map(r => <Option key={r.id} value={r.id}>{r.nom}</Option>)}
          </Select>
          <Select
            placeholder="Toutes les gammes" allowClear style={{ width: 170 }}
            value={gammeFilter} onChange={v => setGammeFilter(v)}
          >
            {GAMMES.filter(g => !['BVF','ALL'].includes(g.value)).map(g => (
              <Option key={g.value} value={g.value}>{g.label}</Option>
            ))}
          </Select>
        </div>
        <Space>
          <Button icon={<DownloadOutlined />} onClick={downloadTemplate}>Modèle Excel</Button>
          <Button icon={<UploadOutlined />} onClick={openImport}>Importer Excel</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openAdd}>Ajouter</Button>
        </Space>
      </div>

      {/* ── Cartes totaux ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12 }}>

        {/* Total général */}
        <div style={{
          background: '#1B5E20', borderRadius: 10, padding: '14px 18px',
          boxShadow: '0 2px 8px rgba(27,94,32,0.25)',
        }}>
          <div style={{ fontSize: 11, color: '#a5d6a7', fontWeight: 700, letterSpacing: 0.8, marginBottom: 4 }}>
            TOTAL — {selectionLabel.toUpperCase()}
          </div>
          <div style={{ fontSize: 26, fontWeight: 800, color: '#fff', lineHeight: 1.1 }}>
            {fmt(totalGeneral)}
          </div>
          <div style={{ fontSize: 11, color: '#81c784', marginTop: 4 }}>
            {filtered.length} ligne{filtered.length > 1 ? 's' : ''}
          </div>
        </div>

        {/* Une carte par gamme présente dans la sélection */}
        {GAMMES.filter(g => totauxParGamme[g.value] != null).map(g => (
          <div
            key={g.value}
            onClick={() => setGammeFilter(gammeFilter === g.value ? undefined : g.value)}
            style={{
              background: gammeFilter === g.value ? g.color : '#fff',
              border: `1.5px solid ${gammeFilter === g.value ? g.color : '#e8f5e9'}`,
              borderRadius: 10, padding: '14px 18px',
              cursor: 'pointer', transition: 'all 0.15s',
              boxShadow: gammeFilter === g.value ? `0 2px 8px ${g.color}40` : '0 1px 3px rgba(0,0,0,0.06)',
            }}
          >
            <div style={{
              fontSize: 11, fontWeight: 700, letterSpacing: 0.8, marginBottom: 4,
              color: gammeFilter === g.value ? 'rgba(255,255,255,0.75)' : g.color,
            }}>
              {g.label.toUpperCase()}
            </div>
            <div style={{
              fontSize: 22, fontWeight: 800, lineHeight: 1.1,
              color: gammeFilter === g.value ? '#fff' : '#1a1a1a',
            }}>
              {fmt(totauxParGamme[g.value])}
            </div>
            <div style={{
              fontSize: 11, marginTop: 4,
              color: gammeFilter === g.value ? 'rgba(255,255,255,0.6)' : '#aaa',
            }}>
              {filtered.filter(o => o.gamme === g.value).length} commercial(aux)
            </div>
          </div>
        ))}
      </div>

      {/* ── Tableau ── */}
      <div style={{ background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.07)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#f1f8e9' }}>
              {['Commercial', 'Zone', 'Rôle', 'Gamme', 'Objectif Volume', ''].map(h => (
                <th key={h} style={{
                  padding: '10px 16px', textAlign: 'left',
                  fontSize: 11, fontWeight: 700, color: '#1B5E20',
                  letterSpacing: 0.5, textTransform: 'uppercase',
                  borderBottom: '1.5px solid #c8e6c9',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: 32, color: '#aaa' }}>Chargement…</td></tr>
            )}
            {!loading && filtered.length === 0 && (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: 32, color: '#aaa' }}>Aucun objectif pour cette sélection</td></tr>
            )}
            {!loading && filtered.map((obj, i) => {
              const emp    = empById[obj.employee_id]
              const region = regions.find(r => r.id === emp?.region_id)
              const gamme  = GAMME_MAP[obj.gamme]
              const zc     = ZONE_COLORS[region?.nom ?? ''] ?? '#888'
              const isEven = i % 2 === 0
              return (
                <tr key={obj.id}
                  style={{ background: isEven ? '#fff' : '#fafff8', borderBottom: '1px solid #e8f5e9' }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#f1f8e9')}
                  onMouseLeave={e => (e.currentTarget.style.background = isEven ? '#fff' : '#fafff8')}
                >
                  <td style={{ padding: '10px 16px', fontWeight: 600, fontSize: 13 }}>
                    {emp ? `${emp.prenom} ${emp.nom}` : obj.employee_id}
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    {region
                      ? <Tag style={{ background: `${zc}12`, color: zc, border: `1px solid ${zc}35`, borderRadius: 4, fontSize: 11, fontWeight: 700 }}>{region.nom}</Tag>
                      : '—'}
                  </td>
                  <td style={{ padding: '10px 16px', fontSize: 12, color: '#666' }}>
                    {emp ? TYPE_POSTE_LABELS[emp.type_poste] : '—'}
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    {gamme
                      ? <Tag style={{ background: `${gamme.color}12`, color: gamme.color, border: `1px solid ${gamme.color}35`, borderRadius: 4, fontSize: 11, fontWeight: 600 }}>{gamme.label}</Tag>
                      : obj.gamme}
                  </td>
                  <td style={{ padding: '10px 16px', fontWeight: 700, fontSize: 14, color: '#1B5E20', textAlign: 'right' }}>
                    {fmt(obj.objectif_volume)}
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <Space size={4}>
                      <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(obj)} />
                      <Button size="small" danger icon={<DeleteOutlined />} onClick={() => onDelete(obj.id)} />
                    </Space>
                  </td>
                </tr>
              )
            })}
            {/* ── Ligne total ── */}
            {!loading && filtered.length > 0 && (
              <tr style={{ background: '#e8f5e9', borderTop: '2px solid #a5d6a7' }}>
                <td colSpan={4} style={{ padding: '10px 16px', fontWeight: 700, fontSize: 12, color: '#1B5E20', letterSpacing: 0.5 }}>
                  TOTAL — {selectionLabel}
                </td>
                <td style={{ padding: '10px 16px', fontWeight: 800, fontSize: 15, color: '#1B5E20', textAlign: 'right' }}>
                  {fmt(totalGeneral)}
                </td>
                <td />
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* ── Modal Import Excel ── */}
      <Modal
        title="Importer des objectifs depuis Excel"
        open={importOpen}
        onCancel={() => { setImportOpen(false); setImportResult(null) }}
        footer={importResult ? [
          <Button key="close" onClick={() => { setImportOpen(false); setImportResult(null) }}>Fermer</Button>
        ] : [
          <Button key="cancel" onClick={() => setImportOpen(false)}>Annuler</Button>,
          <Button key="import" type="primary" icon={<UploadOutlined />}
            loading={importLoading} disabled={!importFile} onClick={onImport}>
            Importer
          </Button>
        ]}
      >
        {!importResult ? (
          <Spin spinning={importLoading}>
            <div style={{ marginBottom: 12, color: '#555', fontSize: 13 }}>
              Période ciblée : <strong>{dayjs(periode).format('MMMM YYYY')}</strong>
            </div>
            <div style={{ marginBottom: 8, fontSize: 13, color: '#555' }}>
              Format attendu : colonnes <strong>Nom</strong>, <strong>Prénom</strong>, puis <strong>FARINE</strong>, <strong>BETAIL</strong>, <strong>VOLAILLE</strong>, <strong>PATES</strong> (en tonnes).
            </div>
            <Button size="small" icon={<DownloadOutlined />} onClick={downloadTemplate} style={{ marginBottom: 16 }}>
              Télécharger le modèle pré-rempli
            </Button>
            <div
              style={{
                border: '2px dashed #a5d6a7', borderRadius: 8, padding: '24px 16px',
                textAlign: 'center', cursor: 'pointer', background: importFile ? '#f1f8e9' : '#fafff8',
              }}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                style={{ display: 'none' }}
                onChange={e => setImportFile(e.target.files?.[0] ?? null)}
              />
              {importFile ? (
                <span style={{ color: '#1B5E20', fontWeight: 600 }}>
                  {importFile.name}
                </span>
              ) : (
                <span style={{ color: '#888' }}>
                  Cliquez pour sélectionner un fichier Excel (.xlsx)
                </span>
              )}
            </div>
          </Spin>
        ) : (
          <div>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
              <div style={{ flex: 1, background: '#e8f5e9', borderRadius: 8, padding: '12px 16px', textAlign: 'center' }}>
                <div style={{ fontSize: 28, fontWeight: 800, color: '#1B5E20' }}>{importResult.created}</div>
                <div style={{ fontSize: 12, color: '#555' }}>Créés</div>
              </div>
              <div style={{ flex: 1, background: '#fff3e0', borderRadius: 8, padding: '12px 16px', textAlign: 'center' }}>
                <div style={{ fontSize: 28, fontWeight: 800, color: '#E65100' }}>{importResult.updated}</div>
                <div style={{ fontSize: 12, color: '#555' }}>Mis à jour</div>
              </div>
              {importResult.errors.length > 0 && (
                <div style={{ flex: 1, background: '#ffebee', borderRadius: 8, padding: '12px 16px', textAlign: 'center' }}>
                  <div style={{ fontSize: 28, fontWeight: 800, color: '#c62828' }}>{importResult.errors.length}</div>
                  <div style={{ fontSize: 12, color: '#555' }}>Erreurs</div>
                </div>
              )}
            </div>
            {importResult.errors.length > 0 && (
              <Alert
                type="warning"
                message="Lignes ignorées"
                description={
                  <ul style={{ margin: 0, paddingLeft: 16 }}>
                    {importResult.errors.map((e, i) => (
                      <li key={i}><strong>{e.nom}</strong> — {e.raison}</li>
                    ))}
                  </ul>
                }
              />
            )}
          </div>
        )}
      </Modal>

      {/* ── Modal Saisie manuelle ── */}
      <Modal
        title={editing ? 'Modifier un objectif' : 'Saisir un objectif'}
        open={modalOpen} onOk={onSave} onCancel={() => setModalOpen(false)}
        okText="Sauvegarder" cancelText="Annuler"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="employee_id" label="Commercial" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="children" disabled={!!editing}>
              {employees.map(e => (
                <Option key={e.id} value={e.id}>
                  {e.prenom} {e.nom} — {regions.find(r => r.id === e.region_id)?.nom ?? ''} — {TYPE_POSTE_LABELS[e.type_poste]}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="gamme" label="Gamme" rules={[{ required: true }]}>
            <Select disabled={!!editing}>
              {GAMMES.map(g => <Option key={g.value} value={g.value}>{g.label}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="objectif_volume" label="Objectif Volume (tonnes)">
            <InputNumber style={{ width: '100%' }} min={0} step={100} />
          </Form.Item>
          <Form.Item name="objectif_ca" label="Objectif CA (FCFA)">
            <InputNumber style={{ width: '100%' }} min={0} step={100000} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
