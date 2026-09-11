import { useEffect, useState, useMemo } from 'react'
import { DatePicker, Select, Tag, Typography, Spin } from 'antd'
import {
  TrophyOutlined, TeamOutlined, FallOutlined,
  RiseOutlined, AlertOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { getSuiviCompte, getRegions } from '../../api/client'

const { Title } = Typography
const { Option } = Select

const fmt    = (n: number) => new Intl.NumberFormat('fr-FR').format(Math.round(n))
const fmtPct = (n: number) => `${n.toFixed(1)} %`

// Semantic color helpers
const colorRecouv = (tx: number) =>
  tx >= 90 ? '#2E7D32' : tx >= 70 ? '#F57F17' : '#C62828'
const bgRecouv = (tx: number) =>
  tx >= 90 ? '#E8F5E9' : tx >= 70 ? '#FFF8E1' : '#FFEBEE'

const colorConv = (tx: number) =>
  tx >= 70 ? '#1565C0' : tx >= 50 ? '#F57F17' : '#C62828'
const bgConv = (tx: number) =>
  tx >= 70 ? '#E3F2FD' : tx >= 50 ? '#FFF8E1' : '#FFEBEE'

const colorInact = (pct: number) =>
  pct <= 20 ? '#2E7D32' : pct <= 40 ? '#F57F17' : '#C62828'

// Rank badge
const RankBadge = ({ rank }: { rank: number }) => (
  <span style={{
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    width: 28, height: 28, borderRadius: '50%',
    fontFamily: "'Barlow Condensed', sans-serif",
    fontWeight: 700, fontSize: 13,
    background: rank === 1 ? '#F9A825' : rank === 2 ? '#CFD8DC' : rank === 3 ? '#BCAAA4' : '#f0f0f0',
    color: rank <= 3 ? '#212121' : '#666',
    flexShrink: 0,
  }}>{rank}</span>
)

// Horizontal progress bar
const Bar = ({ value, max, color, bg }: { value: number; max: number; color: string; bg: string }) => (
  <div style={{ flex: 1, height: 6, borderRadius: 3, background: '#e8e8e8', overflow: 'hidden', minWidth: 60 }}>
    <div style={{
      height: '100%', borderRadius: 3,
      width: `${Math.min(100, max > 0 ? value / max * 100 : 0)}%`,
      background: color, transition: 'width 0.4s ease',
    }} />
  </div>
)

interface SuiviRow {
  employee_id: number
  nom: string
  zone: string
  type_poste: string
  ca_facture: number
  ca_recouvre: number
  taux_recouvrement: number
  nb_clients_actifs: number
  nb_clients_total: number
  nb_clients_inactifs: number
  taux_conversion: number
  pct_inactifs: number
}

const ROLE_LABELS: Record<string, string> = {
  COMMERCIAL: 'Commercial', RCR: 'RCR', SV: 'SV',
  ATC_BV: 'ATC BV', ATC_FARINE: 'ATC Farine',
  RCE: 'RCE', RESP_TECH_FP: 'Resp.Tech.FP',
  RESP_TECH_BV: 'Resp.Tech.BV', DV: 'DV', DCMT: 'DCMT',
}

export default function Suivi() {
  const [periode, setPeriode] = useState(dayjs().format('YYYY-MM'))
  const [regionId, setRegionId] = useState<number | undefined>()
  const [data, setData] = useState<SuiviRow[]>([])
  const [regions, setRegions] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => { getRegions().then(setRegions) }, [])

  useEffect(() => {
    setLoading(true)
    getSuiviCompte({ periode })
      .then(r => setData(r.rows ?? []))
      .finally(() => setLoading(false))
  }, [periode])

  const rows = useMemo(() => {
    if (!regionId) return data
    return data.filter(r => {
      const reg = regions.find(rg => rg.id === regionId)
      return reg && r.zone === reg.nom
    })
  }, [data, regionId, regions])

  // Rankings
  const rankRecouv = useMemo(() =>
    [...rows].filter(r => r.ca_facture > 0)
      .sort((a, b) => b.taux_recouvrement - a.taux_recouvrement),
    [rows])

  const rankConv = useMemo(() =>
    [...rows].filter(r => r.nb_clients_total > 0)
      .sort((a, b) => b.taux_conversion - a.taux_conversion),
    [rows])

  const rankInactifs = useMemo(() =>
    [...rows].filter(r => r.nb_clients_total > 0)
      .sort((a, b) => b.nb_clients_inactifs - a.nb_clients_inactifs),
    [rows])

  // KPIs globaux
  const totalCA      = rows.reduce((s, r) => s + r.ca_facture, 0)
  const totalRec     = rows.reduce((s, r) => s + r.ca_recouvre, 0)
  const txRecovMoy   = totalCA > 0 ? totalRec / totalCA * 100 : 0
  const totalActifs  = rows.reduce((s, r) => s + r.nb_clients_actifs, 0)
  const totalPortef  = rows.reduce((s, r) => s + r.nb_clients_total, 0)
  const txConvMoy    = totalPortef > 0 ? totalActifs / totalPortef * 100 : 0
  const totalInactifs = rows.reduce((s, r) => s + r.nb_clients_inactifs, 0)

  const maxCA = Math.max(...rankRecouv.map(r => r.ca_facture), 1)
  const maxConv = Math.max(...rankConv.map(r => r.nb_clients_total), 1)

  const KPI = ({ icon, label, value, sub, color }: any) => (
    <div style={{
      background: '#fff', borderRadius: 10, padding: '14px 20px',
      boxShadow: '0 1px 4px rgba(0,0,0,0.06)', flex: 1, minWidth: 160,
      borderLeft: `4px solid ${color}`,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <span style={{ color, fontSize: 16 }}>{icon}</span>
        <span style={{ fontSize: 10, fontWeight: 700, color: '#888', textTransform: 'uppercase', letterSpacing: 0.5 }}>{label}</span>
      </div>
      <div style={{ fontFamily: "'Barlow Condensed', sans-serif", fontSize: 26, fontWeight: 700, color: '#1B5E20', lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: '#aaa', marginTop: 3 }}>{sub}</div>}
    </div>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* ── Filtres ── */}
      <div style={{
        background: '#fff', borderRadius: 10, padding: '14px 20px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.07)',
        display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap',
      }}>
        <Title level={5} style={{ margin: 0, color: '#1B5E20' }}>
          Suivi Chargé de Compte
        </Title>
        <DatePicker
          picker="month" value={dayjs(periode)} format="MMMM YYYY"
          onChange={d => d && setPeriode(d.format('YYYY-MM'))}
        />
        <Select placeholder="Toutes les zones" allowClear style={{ width: 150 }}
          value={regionId} onChange={v => setRegionId(v)}>
          {regions.map(r => <Option key={r.id} value={r.id}>{r.nom}</Option>)}
        </Select>
        {loading && <Spin size="small" />}
      </div>

      {/* ── KPIs globaux ── */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <KPI icon={<RiseOutlined />}  label="Taux recouvrement moyen"
          value={fmtPct(txRecovMoy)} sub={`${fmt(totalRec)} F / ${fmt(totalCA)} F`}
          color={colorRecouv(txRecovMoy)} />
        <KPI icon={<TeamOutlined />}  label="Taux conversion portefeuille"
          value={fmtPct(txConvMoy)} sub={`${totalActifs} actifs / ${totalPortef} clients`}
          color={colorConv(txConvMoy)} />
        <KPI icon={<AlertOutlined />} label="Clients inactifs (total)"
          value={totalInactifs} sub={`sur ${totalPortef} en portefeuille`}
          color={totalInactifs > 50 ? '#C62828' : '#F57F17'} />
        <KPI icon={<TrophyOutlined />} label="Commerciaux actifs"
          value={rows.filter(r => r.ca_facture > 0).length}
          sub={`sur ${rows.length} commerciaux`}
          color="#1B5E20" />
      </div>

      {/* ── Rankings côte à côte ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

        {/* Ranking Recouvrement */}
        <div style={{ background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.07)' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #e8f5e9', display: 'flex', alignItems: 'center', gap: 8 }}>
            <RiseOutlined style={{ color: '#1B5E20' }} />
            <span style={{ fontWeight: 700, color: '#1B5E20', fontSize: 13 }}>Classement Recouvrement</span>
          </div>
          <div style={{ padding: '8px 0' }}>
            {rankRecouv.length === 0 && (
              <p style={{ textAlign: 'center', color: '#aaa', padding: 24 }}>Aucune donnée</p>
            )}
            {rankRecouv.map((r, i) => (
              <div key={r.employee_id} style={{
                padding: '8px 16px',
                borderBottom: i < rankRecouv.length - 1 ? '1px solid #f5f5f5' : 'none',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 5 }}>
                  <RankBadge rank={i + 1} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: 12, color: '#222', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.nom}</div>
                    <div style={{ fontSize: 10, color: '#aaa' }}>{r.zone} · {ROLE_LABELS[r.type_poste] ?? r.type_poste}</div>
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <span style={{
                      fontFamily: "'Barlow Condensed', sans-serif",
                      fontSize: 18, fontWeight: 700, color: colorRecouv(r.taux_recouvrement),
                    }}>{fmtPct(r.taux_recouvrement)}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Bar value={r.ca_recouvre} max={maxCA} color={colorRecouv(r.taux_recouvrement)} bg={bgRecouv(r.taux_recouvrement)} />
                  <span style={{ fontSize: 10, color: '#999', whiteSpace: 'nowrap', minWidth: 70, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                    {fmt(r.ca_recouvre)} F
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Ranking Conversion */}
        <div style={{ background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.07)' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #e8f5e9', display: 'flex', alignItems: 'center', gap: 8 }}>
            <FallOutlined style={{ color: '#1565C0', transform: 'rotate(180deg)' }} />
            <span style={{ fontWeight: 700, color: '#1565C0', fontSize: 13 }}>Classement Taux de Conversion</span>
            <span style={{ marginLeft: 'auto', fontSize: 10, color: '#aaa' }}>clients actifs / portefeuille</span>
          </div>
          <div style={{ padding: '8px 0' }}>
            {rankConv.length === 0 && (
              <p style={{ textAlign: 'center', color: '#aaa', padding: 24 }}>Aucune donnée</p>
            )}
            {rankConv.map((r, i) => (
              <div key={r.employee_id} style={{
                padding: '8px 16px',
                borderBottom: i < rankConv.length - 1 ? '1px solid #f5f5f5' : 'none',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 5 }}>
                  <RankBadge rank={i + 1} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: 12, color: '#222', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.nom}</div>
                    <div style={{ fontSize: 10, color: '#aaa' }}>{r.zone} · {ROLE_LABELS[r.type_poste] ?? r.type_poste}</div>
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <span style={{
                      fontFamily: "'Barlow Condensed', sans-serif",
                      fontSize: 18, fontWeight: 700, color: colorConv(r.taux_conversion),
                    }}>{fmtPct(r.taux_conversion)}</span>
                    <div style={{ fontSize: 10, color: '#aaa', fontVariantNumeric: 'tabular-nums' }}>{r.nb_clients_actifs} / {r.nb_clients_total}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Bar value={r.nb_clients_actifs} max={maxConv} color={colorConv(r.taux_conversion)} bg={bgConv(r.taux_conversion)} />
                  <span style={{ fontSize: 10, color: '#999', whiteSpace: 'nowrap', minWidth: 70, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                    {r.nb_clients_inactifs} inactif{r.nb_clients_inactifs > 1 ? 's' : ''}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Tableau clients inactifs ── */}
      <div style={{ background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.07)' }}>
        <div style={{ padding: '12px 20px', borderBottom: '1px solid #f5f5f5', display: 'flex', alignItems: 'center', gap: 8 }}>
          <AlertOutlined style={{ color: '#C62828' }} />
          <span style={{ fontWeight: 700, color: '#C62828', fontSize: 13 }}>Détail des clients inactifs par commercial</span>
          <span style={{ marginLeft: 'auto', fontSize: 11, color: '#aaa' }}>
            Clients en portefeuille sans achat ce mois
          </span>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#fafafa' }}>
                {['Commercial', 'Zone', 'Rôle', 'Portefeuille', 'Actifs', 'Inactifs', '% Inactifs', 'Taux conversion'].map(h => (
                  <th key={h} style={{
                    padding: '9px 14px',
                    textAlign: h === 'Commercial' || h === 'Zone' || h === 'Rôle' ? 'left' : 'right',
                    fontSize: 10, fontWeight: 700, color: '#666',
                    textTransform: 'uppercase', letterSpacing: 0.4,
                    borderBottom: '1.5px solid #e8f5e9', whiteSpace: 'nowrap',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rankInactifs.length === 0 && (
                <tr><td colSpan={8} style={{ textAlign: 'center', padding: 32, color: '#aaa' }}>
                  Aucune donnée de portefeuille pour cette période
                </td></tr>
              )}
              {rankInactifs.map((r, i) => {
                const isEven = i % 2 === 0
                return (
                  <tr key={r.employee_id} style={{
                    background: isEven ? '#fff' : '#fafff8',
                    borderBottom: '1px solid #f0f0f0',
                  }}>
                    <td style={{ padding: '9px 14px', fontWeight: 600, fontSize: 13, color: '#1B5E20' }}>{r.nom}</td>
                    <td style={{ padding: '9px 14px' }}>
                      <Tag style={{ fontSize: 10, fontWeight: 700, background: '#e8f5e9', color: '#1B5E20', border: '1px solid #a5d6a7', borderRadius: 3 }}>
                        {r.zone}
                      </Tag>
                    </td>
                    <td style={{ padding: '9px 14px', fontSize: 11, color: '#888' }}>{ROLE_LABELS[r.type_poste] ?? r.type_poste}</td>
                    <td style={{ padding: '9px 14px', textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{r.nb_clients_total}</td>
                    <td style={{ padding: '9px 14px', textAlign: 'right', fontVariantNumeric: 'tabular-nums', color: '#2E7D32', fontWeight: 600 }}>{r.nb_clients_actifs}</td>
                    <td style={{ padding: '9px 14px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                      <span style={{
                        fontFamily: "'Barlow Condensed', sans-serif",
                        fontSize: 15, fontWeight: 700, color: colorInact(r.pct_inactifs),
                      }}>{r.nb_clients_inactifs}</span>
                    </td>
                    <td style={{ padding: '9px 14px', textAlign: 'right' }}>
                      <span style={{
                        display: 'inline-block', padding: '2px 8px', borderRadius: 10,
                        fontSize: 11, fontWeight: 700, fontVariantNumeric: 'tabular-nums',
                        background: r.pct_inactifs <= 20 ? '#E8F5E9' : r.pct_inactifs <= 40 ? '#FFF8E1' : '#FFEBEE',
                        color: colorInact(r.pct_inactifs),
                      }}>{fmtPct(r.pct_inactifs)}</span>
                    </td>
                    <td style={{ padding: '9px 14px', textAlign: 'right' }}>
                      <span style={{
                        display: 'inline-block', padding: '2px 8px', borderRadius: 10,
                        fontSize: 11, fontWeight: 700, fontVariantNumeric: 'tabular-nums',
                        background: bgConv(r.taux_conversion),
                        color: colorConv(r.taux_conversion),
                      }}>{fmtPct(r.taux_conversion)}</span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
