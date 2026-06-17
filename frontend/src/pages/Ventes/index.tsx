import { useEffect, useState, useMemo } from 'react'
import { DatePicker, Select, Typography, Tag } from 'antd'
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import dayjs from 'dayjs'
import { getVentes, getRegions } from '../../api/client'

const { Title } = Typography
const { Option } = Select

const GAMME_COLORS: Record<string, string> = {
  BETAIL:  '#6A1B9A',
  VOLAILLE:'#00695C',
  FARINE:  '#E65100',
  PATES:   '#1565C0',
}

const fmt    = (n: number) => new Intl.NumberFormat('fr-FR').format(Math.round(n))
const fmtPct = (n: number) => `${n.toFixed(1)} %`

const TX_COLOR = (tx: number) =>
  tx >= 90 ? '#2E7D32' : tx >= 75 ? '#F9A825' : '#C62828'

export default function Ventes() {
  const [periode, setPeriode]       = useState(dayjs().format('YYYY-MM'))
  const [regionId, setRegionId]     = useState<number | undefined>()
  const [gamme, setGamme]           = useState<string | undefined>()
  const [data, setData]             = useState<any>(null)
  const [regions, setRegions]       = useState<any[]>([])
  const [loading, setLoading]       = useState(false)

  useEffect(() => { getRegions().then(setRegions) }, [])

  useEffect(() => {
    setLoading(true)
    getVentes({ periode, region_id: regionId, gamme })
      .then(setData)
      .finally(() => setLoading(false))
  }, [periode, regionId, gamme])

  const pieData = useMemo(() => {
    if (!data?.tonnage_par_gamme) return []
    return Object.entries(data.tonnage_par_gamme).map(([name, value]) => ({ name, value }))
  }, [data])

  const rows: any[] = data?.rows ?? []
  const totaux       = data?.totaux

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* ── Filtres ── */}
      <div style={{
        background: '#fff', borderRadius: 10, padding: '14px 20px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.07)',
        display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap',
      }}>
        <Title level={5} style={{ margin: 0, color: '#1B5E20' }}>Ventes réalisées</Title>
        <DatePicker
          picker="month" value={dayjs(periode)} format="MMMM YYYY"
          onChange={d => d && setPeriode(d.format('YYYY-MM'))}
        />
        <Select placeholder="Toutes les zones" allowClear style={{ width: 150 }}
          value={regionId} onChange={v => setRegionId(v)}>
          {regions.map(r => <Option key={r.id} value={r.id}>{r.nom}</Option>)}
        </Select>
        <Select placeholder="Toutes les gammes" allowClear style={{ width: 160 }}
          value={gamme} onChange={v => setGamme(v)}>
          {(data?.gammes ?? []).map((g: string) => (
            <Option key={g} value={g}>{g}</Option>
          ))}
        </Select>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 16 }}>

        {/* ── Tableau ── */}
        <div style={{ background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.07)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f1f8e9' }}>
                {['Commercial', 'Zone', 'Tonnage', 'Objectif', '% Obj.', 'CA Livré', 'CA Recouvré', 'Tx Recouvr.'].map(h => (
                  <th key={h} style={{
                    padding: '10px 14px', textAlign: h === 'Commercial' || h === 'Zone' ? 'left' : 'right',
                    fontSize: 11, fontWeight: 700, color: '#1B5E20',
                    letterSpacing: 0.5, textTransform: 'uppercase',
                    borderBottom: '1.5px solid #c8e6c9',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={8} style={{ textAlign: 'center', padding: 32, color: '#aaa' }}>Chargement…</td></tr>
              )}
              {!loading && rows.length === 0 && (
                <tr><td colSpan={8} style={{ textAlign: 'center', padding: 32, color: '#aaa' }}>
                  Aucune vente — lancez la synchronisation SAP
                </td></tr>
              )}
              {rows.map((r: any, i: number) => {
                const tx     = r.ca_facture > 0 ? r.ca_recouvre / r.ca_facture * 100 : 0
                const txObj  = r.objectif > 0 ? r.tonnage / r.objectif * 100 : null
                const isEven = i % 2 === 0
                return (
                  <tr key={r.employee_id}
                    style={{ background: isEven ? '#fff' : '#fafff8', borderBottom: '1px solid #e8f5e9' }}
                    onMouseEnter={e => (e.currentTarget.style.background = '#f1f8e9')}
                    onMouseLeave={e => (e.currentTarget.style.background = isEven ? '#fff' : '#fafff8')}
                  >
                    <td style={{ padding: '9px 14px', fontWeight: 600, fontSize: 13 }}>{r.nom}</td>
                    <td style={{ padding: '9px 14px' }}>
                      <Tag style={{
                        fontSize: 10, fontWeight: 700, borderRadius: 3,
                        background: '#e8f5e9', color: '#1B5E20', border: '1px solid #a5d6a7',
                      }}>{r.zone}</Tag>
                    </td>
                    <td style={{ padding: '9px 14px', textAlign: 'right', fontWeight: 600 }}>
                      {fmt(r.tonnage)}
                    </td>
                    <td style={{ padding: '9px 14px', textAlign: 'right', color: '#888' }}>
                      {r.objectif > 0 ? fmt(r.objectif) : <span style={{ color: '#ccc' }}>—</span>}
                    </td>
                    <td style={{ padding: '9px 14px', textAlign: 'right' }}>
                      {txObj !== null ? (
                        <span style={{
                          display: 'inline-block',
                          padding: '2px 8px', borderRadius: 12,
                          fontWeight: 700, fontSize: 12,
                          background: txObj >= 100 ? '#e8f5e9' : txObj >= 90 ? '#fff8e1' : '#ffebee',
                          color: TX_COLOR(txObj),
                          border: `1px solid ${TX_COLOR(txObj)}40`,
                        }}>
                          {fmtPct(txObj)}
                        </span>
                      ) : <span style={{ color: '#ccc' }}>—</span>}
                    </td>
                    <td style={{ padding: '9px 14px', textAlign: 'right', color: '#1565C0', fontWeight: 600 }}>
                      {fmt(r.ca_facture)}
                    </td>
                    <td style={{ padding: '9px 14px', textAlign: 'right', color: '#2E7D32', fontWeight: 600 }}>
                      {fmt(r.ca_recouvre)}
                    </td>
                    <td style={{ padding: '9px 14px', textAlign: 'right' }}>
                      <span style={{ fontWeight: 700, fontSize: 13, color: TX_COLOR(tx) }}>
                        {fmtPct(tx)}
                      </span>
                    </td>
                  </tr>
                )
              })}

              {/* Ligne total */}
              {!loading && totaux && rows.length > 0 && (() => {
                const totalObj   = rows.reduce((s: number, r: any) => s + (r.objectif || 0), 0)
                const txObjTotal = totalObj > 0 ? totaux.tonnage / totalObj * 100 : null
                return (
                  <tr style={{ background: '#e8f5e9', borderTop: '2px solid #a5d6a7' }}>
                    <td colSpan={2} style={{ padding: '10px 14px', fontWeight: 800, fontSize: 12, color: '#1B5E20', letterSpacing: 0.5 }}>
                      TOTAL
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 800, fontSize: 14, color: '#1B5E20' }}>
                      {fmt(totaux.tonnage)}
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 800, fontSize: 13, color: '#888' }}>
                      {totalObj > 0 ? fmt(totalObj) : '—'}
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                      {txObjTotal !== null ? (
                        <span style={{ fontWeight: 800, fontSize: 14, color: TX_COLOR(txObjTotal) }}>
                          {fmtPct(txObjTotal)}
                        </span>
                      ) : '—'}
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 800, fontSize: 14, color: '#1565C0' }}>
                      {fmt(totaux.ca_facture)}
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 800, fontSize: 14, color: '#2E7D32' }}>
                      {fmt(totaux.ca_recouvre)}
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                      <span style={{ fontWeight: 800, fontSize: 14, color: TX_COLOR(totaux.tx_recouvrement) }}>
                        {fmtPct(totaux.tx_recouvrement)}
                      </span>
                    </td>
                  </tr>
                )
              })()}
            </tbody>
          </table>
        </div>

        {/* ── Camembert ── */}
        <div style={{ background: '#fff', borderRadius: 10, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.07)' }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: '#1B5E20', letterSpacing: 0.5, marginBottom: 12, textAlign: 'center' }}>
            TONNAGE PAR GAMME
          </div>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90}
                  label={(props: any) => `${((props.percent ?? 0) * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {pieData.map((entry: any) => (
                    <Cell key={entry.name} fill={GAMME_COLORS[entry.name] ?? '#888'} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: any) => fmt(v)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: 'center', color: '#aaa', padding: 40 }}>Aucune donnée</div>
          )}

          {/* KPIs */}
          {totaux && (
            <div style={{ marginTop: 12, borderTop: '1px solid #e8f5e9', paddingTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { label: 'Total Tonnage',   value: fmt(totaux.tonnage) + ' T',     color: '#1B5E20' },
                { label: 'CA Livré',        value: fmt(totaux.ca_facture) + ' F',  color: '#1565C0' },
                { label: 'CA Recouvré',     value: fmt(totaux.ca_recouvre) + ' F', color: '#2E7D32' },
                { label: 'Tx Recouvrement', value: fmtPct(totaux.tx_recouvrement), color: TX_COLOR(totaux.tx_recouvrement) },
              ].map(k => (
                <div key={k.label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                  <span style={{ color: '#888' }}>{k.label}</span>
                  <span style={{ fontWeight: 700, color: k.color }}>{k.value}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
