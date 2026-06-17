import { useEffect, useState } from 'react'
import {
  Button, Tag, Space, Modal, Form, Input, Select,
  Switch, Typography, Popconfirm, message, Avatar,
} from 'antd'
import { PlusOutlined, EditOutlined, StopOutlined, UserOutlined, DownloadOutlined } from '@ant-design/icons'
import {
  getEmployees, createEmployee, updateEmployee,
  deactivateEmployee, getRegions,
} from '../../api/client'
import type { Employee, Region } from '../../types'
import { TYPE_POSTE_LABELS } from '../../types'

const { Title } = Typography
const { Option } = Select

const ROLE_COLORS: Record<string, string> = {
  RCR:           '#1B5E20',
  SV:            '#2E7D32',
  COMMERCIAL:    '#1565C0',
  ATC_BV:        '#6A1B9A',
  ATC_FARINE:    '#AD1457',
  RCE:           '#E65100',
  RESP_TECH_FP:  '#4E342E',
  RESP_TECH_BV:  '#00695C',
  DV:            '#0D3B12',
  DCMT:          '#0D3B12',
}

const ZONE_COLORS: Record<string, string> = {
  DAKAR:  '#1565C0',
  NORD:   '#6A1B9A',
  CENTRE: '#1B5E20',
  SUD:    '#E65100',
  EXPORT: '#00695C',
}

export default function Employees() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [regions, setRegions]     = useState<Region[]>([])
  const [loading, setLoading]     = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing]     = useState<Employee | null>(null)
  const [zoneFilter, setZoneFilter] = useState<string | null>(null)
  const [form] = Form.useForm()

  const load = () => {
    setLoading(true)
    Promise.all([getEmployees(), getRegions()])
      .then(([emps, regs]) => { setEmployees(emps); setRegions(regs) })
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const regionById = Object.fromEntries(regions.map(r => [r.id, r]))

  const openCreate = () => { setEditing(null); form.resetFields(); setModalOpen(true) }
  const openEdit   = (emp: Employee) => { setEditing(emp); form.setFieldsValue(emp); setModalOpen(true) }

  const onSave = async () => {
    const values = await form.validateFields()
    try {
      editing ? await updateEmployee(editing.id, values) : await createEmployee(values)
      message.success(editing ? 'Employé mis à jour' : 'Employé créé')
      setModalOpen(false)
      load()
    } catch {
      message.error('Erreur lors de la sauvegarde')
    }
  }

  const onDeactivate = async (id: number) => {
    await deactivateEmployee(id)
    message.success('Désactivé')
    load()
  }

  const initials = (e: Employee) =>
    `${e.prenom[0] ?? ''}${e.nom[0] ?? ''}`.toUpperCase()

  const getZone = (emp: Employee) =>
    emp.region?.nom ?? regionById[emp.region_id ?? '']?.nom ?? '—'

  const filtered = zoneFilter
    ? employees.filter(emp => getZone(emp) === zoneFilter)
    : employees

  const exportCSV = () => {
    const header = ['Prénom', 'Nom', 'Rôle', 'Zone', 'Secteur', 'Code SAP', 'Statut']
    const rows = filtered.map(emp => [
      emp.prenom,
      emp.nom,
      TYPE_POSTE_LABELS[emp.type_poste as keyof typeof TYPE_POSTE_LABELS] ?? emp.type_poste,
      getZone(emp),
      emp.secteur ?? '',
      emp.sap_code ?? '',
      emp.actif ? 'Actif' : 'Inactif',
    ])
    const csv = [header, ...rows]
      .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(';'))
      .join('\n')
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `equipe_nma${zoneFilter ? '_' + zoneFilter : ''}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const zoneOptions = Array.from(new Set(
    employees.map(emp => getZone(emp)).filter(z => z !== '—')
  )).sort()

  return (
    <div style={{ background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>

      {/* ── Barre d'en-tête ── */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '16px 24px',
        borderBottom: '1.5px solid #e8f5e9',
        background: '#f9fdf9',
      }}>
        <Title level={4} style={{ margin: 0, color: '#1B5E20' }}>
          Commerciaux & Équipe
          <span style={{ fontSize: 13, fontWeight: 400, color: '#888', marginLeft: 10 }}>
            {filtered.length}{zoneFilter ? ` / ${employees.length}` : ''} membres
          </span>
        </Title>
        <Space>
          <Select
            allowClear
            placeholder="Toutes les zones"
            style={{ width: 180 }}
            value={zoneFilter}
            onChange={v => setZoneFilter(v ?? null)}
            options={zoneOptions.map(z => ({ value: z, label: z }))}
          />
          <Button icon={<DownloadOutlined />} onClick={exportCSV}>
            Export Excel
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            Ajouter
          </Button>
        </Space>
      </div>

      {/* ── Tableau ── */}
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: '#f1f8e9' }}>
            {['Membre', 'Rôle', 'Zone', 'Secteur', 'Code SAP', 'Statut', ''].map(h => (
              <th key={h} style={{
                padding: '10px 16px',
                textAlign: 'left',
                fontSize: 12,
                fontWeight: 700,
                color: '#1B5E20',
                letterSpacing: 0.5,
                textTransform: 'uppercase',
                borderBottom: '1.5px solid #c8e6c9',
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading
            ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: 32, color: '#888' }}>Chargement…</td></tr>
            )
            : filtered.map((emp, i) => {
              const zone = getZone(emp)
              const roleColor = ROLE_COLORS[emp.type_poste] ?? '#555'
              const zoneColor = ZONE_COLORS[zone] ?? '#555'
              const isEven = i % 2 === 0

              return (
                <tr
                  key={emp.id}
                  style={{
                    background: isEven ? '#fff' : '#fafff8',
                    borderBottom: '1px solid #e8f5e9',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#f1f8e9')}
                  onMouseLeave={e => (e.currentTarget.style.background = isEven ? '#fff' : '#fafff8')}
                >
                  {/* Membre */}
                  <td style={{ padding: '11px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <Avatar
                        size={34}
                        style={{ background: roleColor, fontSize: 12, fontWeight: 700, flexShrink: 0 }}
                        icon={!emp.prenom ? <UserOutlined /> : undefined}
                      >
                        {initials(emp)}
                      </Avatar>
                      <span style={{ fontWeight: 600, fontSize: 13, color: '#1a1a1a' }}>
                        {emp.prenom} {emp.nom}
                      </span>
                    </div>
                  </td>

                  {/* Rôle */}
                  <td style={{ padding: '11px 16px' }}>
                    <Tag style={{
                      background: `${roleColor}15`,
                      color: roleColor,
                      border: `1px solid ${roleColor}40`,
                      borderRadius: 4,
                      fontSize: 11,
                      fontWeight: 600,
                    }}>
                      {TYPE_POSTE_LABELS[emp.type_poste as keyof typeof TYPE_POSTE_LABELS]}
                    </Tag>
                  </td>

                  {/* Zone */}
                  <td style={{ padding: '11px 16px' }}>
                    {zone !== '—' ? (
                      <Tag style={{
                        background: `${zoneColor}12`,
                        color: zoneColor,
                        border: `1px solid ${zoneColor}35`,
                        borderRadius: 4,
                        fontSize: 11,
                        fontWeight: 700,
                        letterSpacing: 0.5,
                      }}>
                        {zone}
                      </Tag>
                    ) : <span style={{ color: '#bbb' }}>—</span>}
                  </td>

                  {/* Secteur */}
                  <td style={{ padding: '11px 16px', fontSize: 13, color: '#555' }}>
                    {emp.secteur || <span style={{ color: '#bbb' }}>—</span>}
                  </td>

                  {/* Code SAP */}
                  <td style={{ padding: '11px 16px', fontSize: 12, color: '#888', fontFamily: 'monospace' }}>
                    {emp.sap_code || <span style={{ color: '#bbb' }}>—</span>}
                  </td>

                  {/* Statut */}
                  <td style={{ padding: '11px 16px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '2px 10px',
                      borderRadius: 20,
                      fontSize: 11,
                      fontWeight: 700,
                      background: emp.actif ? '#e8f5e9' : '#ffebee',
                      color: emp.actif ? '#2E7D32' : '#C62828',
                      border: `1px solid ${emp.actif ? '#a5d6a7' : '#ef9a9a'}`,
                    }}>
                      {emp.actif ? 'Actif' : 'Inactif'}
                    </span>
                  </td>

                  {/* Actions */}
                  <td style={{ padding: '11px 16px' }}>
                    <Space size={4}>
                      <Button
                        size="small"
                        icon={<EditOutlined />}
                        onClick={() => openEdit(emp)}
                        style={{ borderColor: '#1B5E20', color: '#1B5E20' }}
                      >
                        Modifier
                      </Button>
                      {emp.actif && (
                        <Popconfirm title="Désactiver cet employé ?" onConfirm={() => onDeactivate(emp.id)}>
                          <Button size="small" icon={<StopOutlined />} danger>
                            Désactiver
                          </Button>
                        </Popconfirm>
                      )}
                    </Space>
                  </td>
                </tr>
              )
            })
          }
        </tbody>
      </table>

      {/* ── Modal ── */}
      <Modal
        title={editing ? 'Modifier employé' : 'Nouvel employé'}
        open={modalOpen}
        onOk={onSave}
        onCancel={() => setModalOpen(false)}
        okText="Sauvegarder"
        cancelText="Annuler"
        width={560}
      >
        <Form form={form} layout="vertical">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
            <Form.Item name="prenom" label="Prénom" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="nom" label="Nom" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
          </div>
          <Form.Item name="email" label="Email">
            <Input />
          </Form.Item>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
            <Form.Item name="type_poste" label="Rôle" rules={[{ required: true }]}>
              <Select>
                {Object.entries(TYPE_POSTE_LABELS).map(([v, t]) => (
                  <Option key={v} value={v}>{t}</Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item name="region_id" label="Zone">
              <Select allowClear>
                {regions.map(r => <Option key={r.id} value={r.id}>{r.nom}</Option>)}
              </Select>
            </Form.Item>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
            <Form.Item name="secteur" label="Secteur">
              <Input />
            </Form.Item>
            <Form.Item name="sap_code" label="Code SAP">
              <Input />
            </Form.Item>
          </div>
          <Form.Item name="sf_id" label="ID Salesforce">
            <Input />
          </Form.Item>
          <Form.Item name="actif" label="Actif" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
