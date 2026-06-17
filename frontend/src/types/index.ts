export type TypePoste =
  | 'RCR' | 'SV' | 'COMMERCIAL' | 'ATC_BV' | 'ATC_FARINE'
  | 'RCE' | 'RESP_TECH_FP' | 'RESP_TECH_BV' | 'DV' | 'DCMT'

export const TYPE_POSTE_LABELS: Record<TypePoste, string> = {
  RCR: 'Resp. Commercial Régional',
  SV: 'Superviseur des Ventes',
  COMMERCIAL: 'Commercial',
  ATC_BV: 'Agent TC Bétail & Volaille',
  ATC_FARINE: 'Agent TC Farine',
  RCE: 'Resp. Commercial Export',
  RESP_TECH_FP: 'Resp. Technique Farine & Pâtes',
  RESP_TECH_BV: 'Resp. Technique Bétail & Volaille',
  DV: 'Directeur des Ventes',
  DCMT: 'Directeur Commercial Marketing Tech.',
}

export type Gamme = 'BVF' | 'PATES' | 'FARINE' | 'NUTRITION_ANIMALE' | 'ALL'
export type StatutBonus = 'BROUILLON' | 'CALCULE' | 'EN_VALIDATION' | 'VALIDE' | 'PAYE'
export type SyncSource = 'SAP' | 'SALESFORCE'
export type SyncStatut = 'EN_COURS' | 'SUCCES' | 'ERREUR'

export interface Region {
  id: number
  nom: string
  type: 'NATIONALE' | 'EXPORT'
}

export interface Employee {
  id: number
  nom: string
  prenom: string
  email?: string
  type_poste: TypePoste
  region_id?: number
  region?: Region
  secteur?: string
  actif: boolean
  sap_code?: string
  sf_id?: string
}

export interface Objective {
  id: number
  employee_id: number
  periode: string
  gamme: Gamme
  objectif_volume?: number
  objectif_ca?: number
}

export interface BonusQualDetail {
  id: number
  critere_code: string
  critere_libelle: string
  valeur_atteinte?: string
  seuil_requis?: string
  montant_max: number
  montant_accorde: number
  eligible: boolean
}

export interface Bonus {
  id: number
  employee_id: number
  period_id: number
  taux_atteinte_global?: number
  taux_atteinte_pates?: number
  taux_atteinte_autres?: number
  volume_realise: number
  volume_objectif: number
  nb_visites: number
  prime_suivi_fixe: number
  prime_quantitative: number
  prime_qualitative: number
  commission_nouvelles_affaires: number
  total: number
  qualitative_eligible: boolean
  statut: StatutBonus
  observations?: string
  calcule_le: string
  qual_details: BonusQualDetail[]
}

export interface BonusPeriod {
  id: number
  periode: string
  statut: StatutBonus
  date_calcul?: string
  valide_par?: string
  date_validation?: string
}

export interface SyncLog {
  id: number
  source: SyncSource
  periode?: string
  started_at: string
  ended_at?: string
  statut: SyncStatut
  nb_records: number
  message?: string
}

export interface DashboardData {
  periode: string
  statut_periode: string
  kpis: {
    nb_employes: number
    nb_calcules: number
    total_primes_fcfa: number
    taux_atteinte_moyen: number
    ca_total_fcfa: number
    taux_recouvrement: number
  }
  top_performers: Array<{
    employee_id: number
    taux_atteinte: number
    total_prime: number
  }>
  by_role: Record<string, {
    count: number
    total_prime: number
    taux_moyen: number
  }>
}
