import { useEffect, useState, useCallback } from 'react'
import {
  Table, DatePicker, Button, Checkbox, Input, Space,
  Typography, Tag, message, Spin, Select, Tooltip,
} from 'antd'
import { SaveOutlined, InfoCircleOutlined, LockOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { getEmployees, getManualCriteria, upsertManualCriteria } from '../../api/client'
import type { Employee } from '../../types'
import { TYPE_POSTE_LABELS } from '../../types'

const { Title } = Typography

interface CriteriaDef {
  code: string
  label: string
  tooltip: string
  roles: string[]
  auto?: boolean  // critère calculé automatiquement (SAP / Salesforce) — affiché en lecture seule
}

const CRITERIA_DEFS: CriteriaDef[] = [
  // ── Critères automatiques (info seulement) ────────────────────────────────
  {
    code: 'AUTO_RECOUVREMENT',
    label: 'Recouvrement ≥ 90%',
    tooltip: 'Calculé automatiquement depuis SAP (montant recouvré M-1 / CA M-1)',
    roles: ['COMMERCIAL', 'RCR', 'SV', 'ATC_BV'],
    auto: true,
  },
  {
    code: 'AUTO_PORTEFEUILLE',
    label: 'Ventes ≥ 70% portefeuille',
    tooltip: 'Calculé automatiquement depuis Salesforce (clients ayant acheté / total portefeuille)',
    roles: ['COMMERCIAL', 'RCR'],
    auto: true,
  },
  {
    code: 'AUTO_CLIENTS_CROISSANCE',
    label: '≥ 70% clients iso/croissance N-1',
    tooltip: 'Calculé automatiquement (clients avec volume ≥ N-1)',
    roles: ['COMMERCIAL', 'RCR', 'SV', 'ATC_BV'],
    auto: true,
  },
  {
    code: 'AUTO_TOP10',
    label: 'Top 10 clients en croissance N-1',
    tooltip: 'Calculé automatiquement (volume top 10 clients vs N-1)',
    roles: ['COMMERCIAL', 'RCR'],
    auto: true,
  },
  {
    code: 'AUTO_VISITES',
    label: 'Visites journalières 100%',
    tooltip: 'Calculé automatiquement depuis Salesforce',
    roles: ['COMMERCIAL', 'SV', 'ATC_BV'],
    auto: true,
  },
  // ── Critères manuels (à cocher chaque mois) ───────────────────────────────
  {
    code: 'PLANNING_AVANT_01',
    label: 'Planning avant le 01 ✎',
    tooltip: 'Planning + tournées envoyé avant le 1er du mois — à cocher manuellement',
    roles: ['COMMERCIAL', 'SV', 'ATC_FARINE'],
  },
  {
    code: 'RAPPORTS_ENVOYES',
    label: 'Rapports & CRM ✎',
    tooltip: '100 % rapports activité + relevés prix/stock envoyés — à cocher manuellement',
    roles: ['COMMERCIAL', 'ATC_BV', 'ATC_FARINE'],
  },
  {
    code: 'PREVISION',
    label: 'Fiabilité prévisions ✎',
    tooltip: 'Cocher si les prévisions du commercial ont été validées (fallback si non saisies dans l\'app)',
    roles: ['COMMERCIAL', 'RCR'],
  },
  {
    code: 'ACCOMPAGNEMENT',
    label: 'Accompagnement ✎',
    tooltip: 'Accompagnement managérial mensuel formalisé (SV → chefs de secteur)',
    roles: ['SV'],
  },
  {
    code: 'RECLAMATIONS_OTIF',
    label: 'Réclamations OTIF ✎',
    tooltip: '100 % des réclamations clients traitées dans les délais',
    roles: ['SV', 'RESP_TECH_FP'],
  },
  {
    code: 'RAPPORT_TECHNIQUE',
    label: 'Rpts techn. ≤ 05 ✎',
    tooltip: 'Rapports techniques mensuels déposés avant le 5 du mois suivant',
    roles: ['RESP_TECH_FP'],
  },
  {
    code: 'RAPPORT_TOURS',
    label: 'Rpt tours clients ✎',
    tooltip: 'Rapport des tours clients envoyé OTIF',
    roles: ['RESP_TECH_FP'],
  },
]

const ROLES_WITH_CRITERIA = new Set([
  'COMMERCIAL', 'RCR', 'SV', 'ATC_BV', 'ATC_FARINE', 'RESP_TECH_FP',
])

const ROLE_ORDER = ['COMMERCIAL', 'RCR', 'SV', 'ATC_BV', 'ATC_FARINE', 'RESP_TECH_FP']

type CriteriaMap = Record<number, Record<string, boolean>>

export default function CriteriaForm() {
  const [periode, setPeriode] = useState(dayjs().format('YYYY-MM'))
  const [validePar, setValidePar] = useState('')
  const [roleFilter, setRoleFilter] = useState<string | null>(null)
  const [employees, setEmployees] = useState<Employee[]>([])
  const [criteria, setCriteria] = useState<CriteriaMap>({})
  const [savedCriteria, setSavedCriteria] = useState<CriteriaMap>({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [emps, mcs] = await Promise.all([
        getEmployees({ actif: true }),
        getManualCriteria(periode),
      ])

      const filtered = (emps as Employee[]).filter(e => ROLES_WITH_CRITERIA.has(e.type_poste))
      setEmployees(filtered)

      const state: CriteriaMap = {}
      for (const emp of filtered) {
        state[emp.id] = {}
        for (const c of CRITERIA_DEFS) {
          if (!c.auto && c.roles.includes(emp.type_poste)) {
            state[emp.id][c.code] = false
          }
        }
      }
      for (const mc of mcs as { employee_id: number; critere_code: string; valeur: boolean }[]) {
        if (state[mc.employee_id]) {
          state[mc.employee_id][mc.critere_code] = mc.valeur
        }
      }
      setCriteria(state)
      setSavedCriteria(JSON.parse(JSON.stringify(state)))
    } finally {
      setLoading(false)
    }
  }, [periode])

  useEffect(() => { loadData() }, [loadData])

  const toggle = (empId: number, code: string, val: boolean) => {
    setCriteria(prev => ({
      ...prev,
      [empId]: { ...prev[empId], [code]: val },
    }))
  }

  const hasPendingChanges = JSON.stringify(criteria) !== JSON.stringify(savedCriteria)

  const save = async () => {
    if (!validePar.trim()) {
      message.warning('Saisir votre nom dans "Validé par" avant d\'enregistrer')
      return
    }
    setSaving(true)
    try {
      const promises: Promise<unknown>[] = []
      for (const [empIdStr, codes] of Object.entries(criteria)) {
        const empId = parseInt(empIdStr)
        for (const [code, val] of Object.entries(codes)) {
          if (val !== (savedCriteria[empId]?.[code] ?? false)) {
            promises.push(upsertManualCriteria({
              employee_id: empId,
              periode,
              critere_code: code,
              valeur: val,
              saisi_par: validePar.trim(),
            }))
          }
        }
      }
      if (promises.length === 0) {
        message.info('Aucune modification')
        return
      }
      await Promise.all(promises)
      message.success(`${promises.length} critère(s) enregistré(s)`)
      setSavedCriteria(JSON.parse(JSON.stringify(criteria)))
    } catch {
      message.error('Erreur lors de l\'enregistrement')
    } finally {
      setSaving(false)
    }
  }

  const sorted = [...employees]
    .filter(e => !roleFilter || e.type_poste === roleFilter)
    .sort((a, b) => {
      const ra = ROLE_ORDER.indexOf(a.type_poste)
      const rb = ROLE_ORDER.indexOf(b.type_poste)
      if (ra !== rb) return ra - rb
      return `${a.nom} ${a.prenom}`.localeCompare(`${b.nom} ${b.prenom}`)
    })

  const activeRoles = new Set(sorted.map(e => e.type_poste))
  const visibleCriteria = CRITERIA_DEFS.filter(c => c.roles.some(r => activeRoles.has(r as any)))

  const isModified = (empId: number) =>
    Object.entries(criteria[empId] || {}).some(
      ([code, val]) => val !== (savedCriteria[empId]?.[code] ?? false)
    )

  const columns = [
    {
      title: 'Commercial',
      key: 'nom',
      fixed: 'left' as const,
      width: 170,
      render: (_: unknown, e: Employee) => (
        <span style={{ fontWeight: isModified(e.id) ? 600 : 400 }}>
          {e.prenom} {e.nom}
        </span>
      ),
    },
    {
      title: 'Rôle',
      key: 'role',
      fixed: 'left' as const,
      width: 120,
      render: (_: unknown, e: Employee) => (
        <Tag color="geekblue" style={{ fontSize: 11 }}>
          {e.type_poste}
        </Tag>
      ),
    },
    ...visibleCriteria.map(c => ({
      title: (
        <Tooltip title={c.tooltip}>
          <span style={{ fontSize: 11, cursor: 'help', whiteSpace: 'nowrap', color: c.auto ? '#aaa' : undefined }}>
            {c.auto && <LockOutlined style={{ marginRight: 3, fontSize: 10 }} />}
            {c.label} <InfoCircleOutlined style={{ opacity: 0.4, fontSize: 10 }} />
          </span>
        </Tooltip>
      ),
      key: c.code,
      width: 140,
      align: 'center' as const,
      render: (_: unknown, e: Employee) => {
        if (!c.roles.includes(e.type_poste)) {
          return <span style={{ color: '#ddd' }}>–</span>
        }
        if (c.auto) {
          return (
            <Tooltip title="Calculé automatiquement (SAP / Salesforce)">
              <LockOutlined style={{ color: '#ccc', fontSize: 12 }} />
            </Tooltip>
          )
        }
        const checked = criteria[e.id]?.[c.code] ?? false
        const saved = savedCriteria[e.id]?.[c.code] ?? false
        return (
          <Checkbox
            checked={checked}
            onChange={ev => toggle(e.id, c.code, ev.target.checked)}
            style={checked !== saved ? { accentColor: '#E65100' } : undefined}
          />
        )
      },
    })),
  ]

  const totalChecked = Object.values(criteria).reduce(
    (sum, codes) => sum + Object.values(codes).filter(Boolean).length, 0
  )

  return (
    <div style={{ padding: 24, background: '#fff', borderRadius: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <Title level={4} style={{ margin: 0 }}>Critères qualitatifs — saisie</Title>
          <span style={{ color: '#888', fontSize: 12 }}>
            {totalChecked} critère(s) cochés sur {sorted.length} employé(s)
            {hasPendingChanges && <span style={{ color: '#E65100', marginLeft: 8 }}>● modifications en attente</span>}
          </span>
        </div>
        <Space>
          <DatePicker
            picker="month"
            value={dayjs(periode)}
            format="MMMM YYYY"
            onChange={d => d && setPeriode(d.format('YYYY-MM'))}
          />
          <Select
            allowClear
            placeholder="Tous les rôles"
            style={{ width: 170 }}
            value={roleFilter}
            onChange={v => setRoleFilter(v ?? null)}
            options={[
              { value: 'COMMERCIAL',    label: 'Commercial' },
              { value: 'RCR',           label: 'RCR' },
              { value: 'SV',            label: 'Superviseur' },
              { value: 'ATC_BV',        label: 'ATC' },
              { value: 'RESP_TECH_FP',  label: 'Resp. Tech. FP' },
            ]}
          />
          <Input
            placeholder="Validé par"
            value={validePar}
            onChange={e => setValidePar(e.target.value)}
            style={{ width: 160 }}
          />
          <Button
            type="primary"
            icon={<SaveOutlined />}
            loading={saving}
            disabled={!hasPendingChanges}
            onClick={save}
          >
            Enregistrer
          </Button>
        </Space>
      </div>

      <Spin spinning={loading}>
        <Table
          dataSource={sorted}
          columns={columns}
          rowKey="id"
          size="small"
          scroll={{ x: 'max-content' }}
          pagination={false}
          rowClassName={(e: Employee) => isModified(e.id) ? 'row-modified' : ''}
        />
      </Spin>

      <div style={{ marginTop: 12, fontSize: 12, color: '#aaa' }}>
        Visites & CRM sont calculés automatiquement depuis Salesforce. Seuls les critères ci-dessus nécessitent une saisie manuelle chaque mois.
      </div>
    </div>
  )
}
