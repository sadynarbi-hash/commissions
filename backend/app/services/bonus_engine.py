from __future__ import annotations
"""
Moteur de calcul des primes NMA 2026.
Chaque rôle a sa propre logique conforme au document SYSTEME DE PRIMES V12.
"""
from dataclasses import dataclass, field
from typing import Optional
from ..models.employee import TypePoste


@dataclass
class QualCriterion:
    code: str
    libelle: str
    montant_max: float
    eligible: bool = False
    valeur_atteinte: Optional[str] = None
    seuil_requis: Optional[str] = None

    @property
    def montant_accorde(self) -> float:
        return self.montant_max if self.eligible else 0.0


@dataclass
class BonusResult:
    employee_id: int
    periode: str
    type_poste: str

    taux_atteinte_global: Optional[float] = None
    taux_atteinte_pates: Optional[float] = None
    taux_atteinte_autres: Optional[float] = None

    prime_suivi_fixe: float = 0.0
    prime_quantitative: float = 0.0
    prime_qualitative: float = 0.0
    commission_nouvelles_affaires: float = 0.0
    qualitative_eligible: bool = False

    criteria: list[QualCriterion] = field(default_factory=list)

    @property
    def total(self) -> float:
        return (
            self.prime_suivi_fixe
            + self.prime_quantitative
            + self.prime_qualitative
            + self.commission_nouvelles_affaires
        )

    def to_detail_dict(self) -> dict:
        return {
            "taux_global": self.taux_atteinte_global,
            "taux_pates": self.taux_atteinte_pates,
            "taux_autres": self.taux_atteinte_autres,
            "prime_suivi_fixe": self.prime_suivi_fixe,
            "prime_quantitative": self.prime_quantitative,
            "prime_qualitative": self.prime_qualitative,
            "commission": self.commission_nouvelles_affaires,
            "total": self.total,
            "qualitative_eligible": self.qualitative_eligible,
            "criteria": [
                {
                    "code": c.code,
                    "libelle": c.libelle,
                    "montant_max": c.montant_max,
                    "montant_accorde": c.montant_accorde,
                    "eligible": c.eligible,
                    "valeur_atteinte": c.valeur_atteinte,
                    "seuil_requis": c.seuil_requis,
                }
                for c in self.criteria
            ],
        }


# Paliers quantitatifs communs
PALIERS_STANDARD = [(0.90, 250_000), (1.00, 350_000), (1.15, 500_000)]
PALIERS_ATC_BV = [(0.90, 150_000), (1.00, 250_000), (1.15, 350_000)]
PALIERS_RESP_TECH_FP = [(0.90, 175_000), (1.00, 225_000), (1.15, 300_000)]
PALIERS_SV_PATES = [(0.90, 90_000), (1.00, 175_000), (1.15, 210_000)]
PALIERS_SV_AUTRES = [(0.90, 60_000), (1.00, 75_000), (1.15, 90_000)]

# V12 — Commerciaux : prime quantitative en % du CA (montant facturé)
TAUX_COMMERCIAL_BVF   = [(0.90, 0.0005), (1.00, 0.0010), (1.15, 0.0020)]  # 0,05% / 0,10% / 0,20%
TAUX_COMMERCIAL_PATES = [(0.90, 0.0020), (1.00, 0.0035), (1.15, 0.0040)]  # 0,20% / 0,35% / 0,40%


def _palier(taux: float, paliers: list[tuple]) -> float:
    """Retourne le montant du palier atteint (le plus élevé possible)."""
    montant = 0.0
    for seuil, valeur in sorted(paliers):
        if taux >= seuil:
            montant = valeur
    return montant


def _taux(realise: float, objectif: float) -> float:
    if objectif <= 0:
        return 0.0
    return min(realise / objectif, 2.0)  # plafonné à 200% pour éviter aberrations


def calculate_bonus(
    employee_id: int,
    type_poste: TypePoste,
    periode: str,
    # Données de ventes (from SAP)
    volume_realise: float = 0,
    volume_objectif: float = 0,
    volume_pates_realise: float = 0,
    volume_pates_objectif: float = 0,
    volume_autres_realise: float = 0,
    volume_autres_objectif: float = 0,
    montant_facture: float = 0,    # CA M-1 (base recouvrement)
    montant_recouvre: float = 0,   # montant récupéré M-1
    montant_facture_m: float = 0,  # CA mois M (base prime quanti V12)
    # Données prévisions
    prevision: float = 0,
    realise_pour_prevision: float = 0,
    # Données portefeuille
    nb_clients_portefeuille: int = 0,
    nb_clients_avec_achat: int = 0,
    nb_clients_visite: int = 0,
    nb_clients_croissance: int = 0,
    nb_clients_actifs: int = 0,
    top_clients_volume: float = 0,
    top_clients_volume_n1: float = 0,
    # Données visites (from Salesforce)
    nb_visites_realisees: int = 0,
    nb_visites_objectif: int = 0,
    nb_fermes_par_jour_moy: float = 0,
    taux_crm_commandes: float = 0,
    taux_crm_visites: float = 0,
    taux_rapport_activities: float = 0,
    taux_kpis_ferme: float = 0,
    # Critères manuels (booléens)
    planning_envoye_avant_01: bool = False,
    rapport_technique_envoye: bool = False,
    rapport_tour_clients: bool = False,
    reclamations_traitees_otif: bool = False,
    accompagnement_managerial: bool = False,
    # Nouvelles affaires
    ca_nouvelles_affaires: float = 0,
) -> BonusResult:

    result = BonusResult(
        employee_id=employee_id,
        type_poste=type_poste.value,
        periode=periode,
    )

    if type_poste == TypePoste.RCR:
        _calc_rcr(result, volume_realise, volume_objectif, montant_facture, montant_recouvre,
                  prevision, realise_pour_prevision, nb_clients_portefeuille,
                  nb_clients_avec_achat, nb_clients_croissance, top_clients_volume,
                  top_clients_volume_n1, taux_crm_commandes, taux_crm_visites)

    elif type_poste == TypePoste.SV:
        _calc_sv(result, volume_pates_realise, volume_pates_objectif,
                 volume_autres_realise, volume_autres_objectif,
                 planning_envoye_avant_01, nb_clients_portefeuille, nb_clients_avec_achat,
                 nb_clients_croissance, accompagnement_managerial,
                 taux_crm_commandes, taux_crm_visites, reclamations_traitees_otif)

    elif type_poste == TypePoste.COMMERCIAL:
        _calc_commercial(result, volume_realise, volume_objectif,
                         montant_facture_m or montant_facture,  # CA M pour prime quanti
                         montant_facture, montant_recouvre,     # CA M-1 pour recouvrement
                         prevision, realise_pour_prevision,
                         nb_clients_portefeuille, nb_clients_avec_achat,
                         nb_clients_croissance, top_clients_volume, top_clients_volume_n1,
                         nb_visites_realisees, nb_visites_objectif, planning_envoye_avant_01,
                         taux_crm_commandes, taux_crm_visites, taux_rapport_activities,
                         ca_nouvelles_affaires,
                         pates_commercial=(volume_pates_objectif > 0 and volume_pates_objectif > volume_autres_objectif))

    elif type_poste == TypePoste.ATC_BV:
        _calc_atc(result, volume_realise, volume_objectif, montant_facture, montant_recouvre,
                  nb_clients_portefeuille, nb_clients_croissance, nb_clients_actifs,
                  top_clients_volume, top_clients_volume_n1,
                  nb_visites_realisees, nb_visites_objectif, nb_fermes_par_jour_moy,
                  planning_envoye_avant_01, taux_kpis_ferme, taux_rapport_activities,
                  ca_nouvelles_affaires)

    elif type_poste == TypePoste.ATC_FARINE:
        _calc_atc_farine(result, volume_realise, volume_objectif, montant_facture, montant_recouvre,
                         nb_clients_portefeuille, nb_clients_avec_achat, nb_clients_croissance,
                         top_clients_volume, top_clients_volume_n1,
                         nb_visites_realisees, nb_visites_objectif,
                         planning_envoye_avant_01, taux_crm_commandes, taux_crm_visites,
                         taux_rapport_activities, ca_nouvelles_affaires)

    elif type_poste == TypePoste.RCE:
        _calc_rce(result, volume_realise, volume_objectif, prevision, realise_pour_prevision,
                  nb_clients_portefeuille, nb_clients_avec_achat, nb_clients_croissance,
                  top_clients_volume, top_clients_volume_n1)

    elif type_poste == TypePoste.RESP_TECH_FP:
        _calc_resp_tech_fp(result, volume_realise, volume_objectif,
                           planning_envoye_avant_01, reclamations_traitees_otif,
                           rapport_technique_envoye, rapport_tour_clients)

    # RESP_TECH_BV, DV, DCMT : pas de primes définies dans ce document
    result.prime_qualitative = sum(c.montant_accorde for c in result.criteria)
    return result


# ──────────────────────────────────────────────────────────
# RCR
# ──────────────────────────────────────────────────────────
def _calc_rcr(r: BonusResult, vol_real, vol_obj, mnt_fact, mnt_recouv,
              prevision, real_prev, nb_portefeuille, nb_achat, nb_croissance,
              top_vol, top_vol_n1, taux_crm_cmd, taux_crm_vis):
    taux = _taux(vol_real, vol_obj)
    r.taux_atteinte_global = round(taux * 100, 2)
    r.prime_quantitative = _palier(taux, PALIERS_STANDARD)

    qualif = taux >= 0.90
    r.qualitative_eligible = qualif

    taux_recouv = _taux(mnt_recouv, mnt_fact) if mnt_fact > 0 else 0
    taux_prev = min(_taux(real_prev, prevision), _taux(prevision, real_prev)) if prevision > 0 else 0
    pct_achat = _taux(nb_achat, nb_portefeuille) if nb_portefeuille > 0 else 0
    pct_crois = _taux(nb_croissance, nb_portefeuille) if nb_portefeuille > 0 else 0
    taux_crm = min(taux_crm_cmd, taux_crm_vis)

    r.criteria = [
        QualCriterion("RECOUVREMENT", "Recouvrement ≥ 90%", 40_000,
                      eligible=qualif and taux_recouv >= 0.90,
                      valeur_atteinte=f"{taux_recouv*100:.1f}%", seuil_requis="90%"),
        QualCriterion("PREVISION", "Fiabilité prévisions ≥ 90%", 30_000,
                      eligible=qualif and taux_prev >= 0.90,
                      valeur_atteinte=f"{taux_prev*100:.1f}%", seuil_requis="90%"),
        QualCriterion("PORTEFEUILLE_ACHAT", "Ventes ≥ 80% du portefeuille", 40_000,
                      eligible=qualif and pct_achat >= 0.80,
                      valeur_atteinte=f"{pct_achat*100:.1f}%", seuil_requis="80%"),
        QualCriterion("CLIENTS_CROISSANCE", "≥ 70% clients iso/croissance vs N-1", 30_000,
                      eligible=qualif and pct_crois >= 0.70,
                      valeur_atteinte=f"{pct_crois*100:.1f}%", seuil_requis="70%"),
        QualCriterion("TOP15_CROISSANCE", "Volume top 15 clients en croissance vs N-1", 30_000,
                      eligible=qualif and top_vol >= top_vol_n1,
                      valeur_atteinte=f"{top_vol:,.0f}", seuil_requis=f"≥ {top_vol_n1:,.0f}"),
        QualCriterion("CRM_CONFORMITE", "100% visites & commandes saisies CRM", 30_000,
                      eligible=qualif and taux_crm >= 1.0,
                      valeur_atteinte=f"{taux_crm*100:.1f}%", seuil_requis="100%"),
    ]


# ──────────────────────────────────────────────────────────
# SV
# ──────────────────────────────────────────────────────────
def _calc_sv(r: BonusResult, vol_pates_real, vol_pates_obj, vol_autres_real, vol_autres_obj,
             planning_avant_01, nb_portefeuille, nb_achat, nb_croissance,
             accompagnement, taux_crm_cmd, taux_crm_vis, reclamations_otif):
    taux_p = _taux(vol_pates_real, vol_pates_obj)
    taux_a = _taux(vol_autres_real, vol_autres_obj)
    r.taux_atteinte_pates = round(taux_p * 100, 2)
    r.taux_atteinte_autres = round(taux_a * 100, 2)
    total_obj = vol_pates_obj + vol_autres_obj
    total_real = vol_pates_real + vol_autres_real
    r.taux_atteinte_global = round(_taux(total_real, total_obj) * 100, 2) if total_obj > 0 else None
    r.prime_quantitative = _palier(taux_p, PALIERS_SV_PATES) + _palier(taux_a, PALIERS_SV_AUTRES)

    qualif = taux_p >= 0.90 and taux_a >= 0.90
    r.qualitative_eligible = qualif

    pct_achat = _taux(nb_achat, nb_portefeuille) if nb_portefeuille > 0 else 0
    pct_crois = _taux(nb_croissance, nb_portefeuille) if nb_portefeuille > 0 else 0
    taux_crm = min(taux_crm_cmd, taux_crm_vis)

    r.criteria = [
        QualCriterion("PLANNING_AVANT_01", "Plan facturation + tournées envoyé avant le 01", 20_000,
                      eligible=qualif and planning_avant_01,
                      valeur_atteinte="Oui" if planning_avant_01 else "Non", seuil_requis="Oui"),
        QualCriterion("PORTEFEUILLE_ACHAT", "Ventes ≥ 70% du portefeuille", 25_000,
                      eligible=qualif and pct_achat >= 0.70,
                      valeur_atteinte=f"{pct_achat*100:.1f}%", seuil_requis="70%"),
        QualCriterion("CLIENTS_PATES_CROISSANCE", "≥ 70% clients Pâtes iso/croissance vs N-1", 25_000,
                      eligible=qualif and pct_crois >= 0.70,
                      valeur_atteinte=f"{pct_crois*100:.1f}%", seuil_requis="70%"),
        QualCriterion("ACCOMPAGNEMENT", "Accompagnement managérial mensuel formalisé", 20_000,
                      eligible=qualif and accompagnement,
                      valeur_atteinte="Oui" if accompagnement else "Non", seuil_requis="Oui"),
        QualCriterion("CRM_CONFORMITE", "100% visites & commandes CRM (chefs secteurs)", 35_000,
                      eligible=qualif and taux_crm >= 1.0,
                      valeur_atteinte=f"{taux_crm*100:.1f}%", seuil_requis="100%"),
        QualCriterion("RECLAMATIONS", "100% réclamations clients traitées", 25_000,
                      eligible=qualif and reclamations_otif,
                      valeur_atteinte="Oui" if reclamations_otif else "Non", seuil_requis="Oui"),
    ]


# ──────────────────────────────────────────────────────────
# COMMERCIAL
# ──────────────────────────────────────────────────────────
def _calc_commercial(r: BonusResult, vol_real, vol_obj,
                     mnt_fact_m,           # CA mois M → prime quantitative V12
                     mnt_fact_m1,          # CA mois M-1 → base recouvrement
                     mnt_recouv,
                     prevision, real_prev, nb_portefeuille, nb_achat, nb_croissance,
                     top_vol, top_vol_n1, nb_visites_real, nb_visites_obj,
                     planning_avant_01, taux_crm_cmd, taux_crm_vis, taux_rapports,
                     ca_nouvelles_affaires, pates_commercial: bool = False):
    r.prime_suivi_fixe = 100_000
    r.commission_nouvelles_affaires = round(ca_nouvelles_affaires * 0.005, 2)

    taux = _taux(vol_real, vol_obj)
    r.taux_atteinte_global = round(taux * 100, 2)

    # V12 : prime quantitative = % du CA mois M selon palier
    paliers_taux = TAUX_COMMERCIAL_PATES if pates_commercial else TAUX_COMMERCIAL_BVF
    taux_commission = _palier(taux, paliers_taux)
    r.prime_quantitative = round(mnt_fact_m * taux_commission, 0)

    qualif = taux >= 0.90
    r.qualitative_eligible = qualif

    taux_recouv = _taux(mnt_recouv, mnt_fact_m1) if mnt_fact_m1 > 0 else 0
    taux_prev = min(_taux(real_prev, prevision), _taux(prevision, real_prev)) if prevision > 0 else 0
    pct_achat = _taux(nb_achat, nb_portefeuille) if nb_portefeuille > 0 else 0
    pct_crois = _taux(nb_croissance, nb_portefeuille) if nb_portefeuille > 0 else 0
    taux_visites = _taux(nb_visites_real, nb_visites_obj) if nb_visites_obj > 0 else 0
    taux_crm = min(taux_crm_cmd, taux_crm_vis)

    r.criteria = [
        QualCriterion("RECOUVREMENT", "Recouvrement ≥ 90%", 30_000,
                      eligible=qualif and taux_recouv >= 0.90,
                      valeur_atteinte=f"{taux_recouv*100:.1f}%", seuil_requis="90%"),
        QualCriterion("PREVISION", "Fiabilité prévisions ≥ 90%", 20_000,
                      eligible=qualif and taux_prev >= 0.90,
                      valeur_atteinte=f"{taux_prev*100:.1f}%", seuil_requis="90%"),
        QualCriterion("PORTEFEUILLE_ACHAT", "Ventes ≥ 70% du portefeuille visité", 20_000,
                      eligible=qualif and pct_achat >= 0.70,
                      valeur_atteinte=f"{pct_achat*100:.1f}%", seuil_requis="70%"),
        QualCriterion("CLIENTS_CROISSANCE", "≥ 70% clients iso/croissance vs N-1", 20_000,
                      eligible=qualif and pct_crois >= 0.70,
                      valeur_atteinte=f"{pct_crois*100:.1f}%", seuil_requis="70%"),
        QualCriterion("TOP10_CROISSANCE", "Volume top 10 clients en croissance vs N-1", 20_000,
                      eligible=qualif and top_vol >= top_vol_n1,
                      valeur_atteinte=f"{top_vol:,.0f}", seuil_requis=f"≥ {top_vol_n1:,.0f}"),
        QualCriterion("VISITES_JOURNALIERES", "100% objectif visites journalières + planning avant le 01", 20_000,
                      eligible=qualif and taux_visites >= 1.0 and planning_avant_01,
                      valeur_atteinte=f"{taux_visites*100:.1f}%", seuil_requis="100%"),
        QualCriterion("RAPPORTS_CRM", "100% rapports + relevés prix/stock + CRM", 20_000,
                      eligible=qualif and taux_crm >= 1.0 and taux_rapports >= 1.0,
                      valeur_atteinte=f"CRM:{taux_crm*100:.0f}% / Rapports:{taux_rapports*100:.0f}%",
                      seuil_requis="100%"),
    ]


# ──────────────────────────────────────────────────────────
# ATC Bétail & Volaille / Farine
# ──────────────────────────────────────────────────────────
def _calc_atc(r: BonusResult, vol_real, vol_obj, mnt_fact, mnt_recouv,
              nb_portefeuille, nb_croissance, nb_actifs, top_vol, top_vol_n1,
              nb_visites_real, nb_visites_obj, nb_fermes_moy,
              planning_avant_01, taux_kpis, taux_rapports, ca_nouvelles_affaires):
    r.prime_suivi_fixe = 100_000
    r.commission_nouvelles_affaires = round(ca_nouvelles_affaires * 0.005, 2)

    taux = _taux(vol_real, vol_obj)
    r.taux_atteinte_global = round(taux * 100, 2)
    r.prime_quantitative = _palier(taux, PALIERS_ATC_BV)

    qualif = taux >= 0.90
    r.qualitative_eligible = qualif

    taux_recouv = _taux(mnt_recouv, mnt_fact) if mnt_fact > 0 else 0
    pct_crois = _taux(nb_croissance, nb_portefeuille) if nb_portefeuille > 0 else 0
    pct_actifs = _taux(nb_actifs, nb_portefeuille) if nb_portefeuille > 0 else 0
    taux_visites = _taux(nb_visites_real, nb_visites_obj) if nb_visites_obj > 0 else 0

    r.criteria = [
        QualCriterion("RECOUVREMENT", "Recouvrement ≥ 90%", 30_000,
                      eligible=qualif and taux_recouv >= 0.90,
                      valeur_atteinte=f"{taux_recouv*100:.1f}%", seuil_requis="90%"),
        QualCriterion("KPIS_FERME", "Remontée journalière 100% KPIs techniques ferme", 40_000,
                      eligible=qualif and taux_kpis >= 1.0,
                      valeur_atteinte=f"{taux_kpis*100:.1f}%", seuil_requis="100%"),
        QualCriterion("CLIENTS_CROISSANCE", "≥ 70% clients fermes iso/croissance vs N-1", 30_000,
                      eligible=qualif and pct_crois >= 0.70,
                      valeur_atteinte=f"{pct_crois*100:.1f}%", seuil_requis="70%"),
        QualCriterion("CLIENTS_ACTIFS", "≥ 70% clients fermes actifs dans le portefeuille", 30_000,
                      eligible=qualif and pct_actifs >= 0.70,
                      valeur_atteinte=f"{pct_actifs*100:.1f}%", seuil_requis="70%"),
        QualCriterion("TOP10_FERMES", "Top 10 fermes en croissance volume vs N-1", 20_000,
                      eligible=qualif and top_vol >= top_vol_n1,
                      valeur_atteinte=f"{top_vol:,.0f}", seuil_requis=f"≥ {top_vol_n1:,.0f}"),
        QualCriterion("VISITES_FERMES", "100% visites journalières (12/j, min 3 fermes) + planning avant 01", 30_000,
                      eligible=qualif and taux_visites >= 1.0 and nb_fermes_moy >= 3 and planning_avant_01,
                      valeur_atteinte=f"{nb_visites_real} visites / {nb_fermes_moy:.1f} fermes/j",
                      seuil_requis="12 visites/j + 3 fermes/j"),
        QualCriterion("RAPPORTS", "Rapports activités hebdo/mensuels + réclamations CRM", 20_000,
                      eligible=qualif and taux_rapports >= 1.0,
                      valeur_atteinte=f"{taux_rapports*100:.1f}%", seuil_requis="100%"),
    ]


# ──────────────────────────────────────────────────────────
# RCE
# ──────────────────────────────────────────────────────────
def _calc_rce(r: BonusResult, vol_real, vol_obj, prevision, real_prev,
              nb_portefeuille, nb_achat, nb_croissance, top_vol, top_vol_n1):
    taux = _taux(vol_real, vol_obj)
    r.taux_atteinte_global = round(taux * 100, 2)
    r.prime_quantitative = _palier(taux, PALIERS_STANDARD)

    qualif = taux >= 0.90
    r.qualitative_eligible = qualif

    taux_prev = min(_taux(real_prev, prevision), _taux(prevision, real_prev)) if prevision > 0 else 0
    pct_achat = _taux(nb_achat, nb_portefeuille) if nb_portefeuille > 0 else 0
    pct_crois = _taux(nb_croissance, nb_portefeuille) if nb_portefeuille > 0 else 0

    r.criteria = [
        QualCriterion("PREVISION", "Fiabilité prévisions ≥ 90%", 30_000,
                      eligible=qualif and taux_prev >= 0.90,
                      valeur_atteinte=f"{taux_prev*100:.1f}%", seuil_requis="90%"),
        QualCriterion("PORTEFEUILLE_ACHAT", "Ventes ≥ 80% du portefeuille", 50_000,
                      eligible=qualif and pct_achat >= 0.80,
                      valeur_atteinte=f"{pct_achat*100:.1f}%", seuil_requis="80%"),
        QualCriterion("CLIENTS_CROISSANCE", "≥ 70% clients iso/croissance vs N-1", 50_000,
                      eligible=qualif and pct_crois >= 0.70,
                      valeur_atteinte=f"{pct_crois*100:.1f}%", seuil_requis="70%"),
        QualCriterion("TOP5_CROISSANCE", "Volume top 5 clients en croissance vs N-1", 30_000,
                      eligible=qualif and top_vol >= top_vol_n1,
                      valeur_atteinte=f"{top_vol:,.0f}", seuil_requis=f"≥ {top_vol_n1:,.0f}"),
    ]


# ──────────────────────────────────────────────────────────
# Responsable Technique Farine & Pâtes
# ──────────────────────────────────────────────────────────
def _calc_resp_tech_fp(r: BonusResult, vol_real, vol_obj,
                       visites_planifiees, reclamations_otif,
                       rapport_technique, rapport_tour_clients):
    taux = _taux(vol_real, vol_obj)
    r.taux_atteinte_global = round(taux * 100, 2)
    r.prime_quantitative = _palier(taux, PALIERS_RESP_TECH_FP)

    qualif = taux >= 0.90
    r.qualitative_eligible = qualif

    r.criteria = [
        QualCriterion("VISITES_CRM", "100% visites planifiées et commandes CRM", 25_000,

                      eligible=qualif and visites_planifiees,
                      valeur_atteinte="Oui" if visites_planifiees else "Non", seuil_requis="Oui"),
        QualCriterion("RECLAMATIONS_OTIF", "Réclamations traitées OTIF", 25_000,
                      eligible=qualif and reclamations_otif,
                      valeur_atteinte="Oui" if reclamations_otif else "Non", seuil_requis="Oui"),
        QualCriterion("RAPPORT_TECHNIQUE", "Rapports techniques mensuels envoyés avant le 05", 25_000,
                      eligible=qualif and rapport_technique,
                      valeur_atteinte="Oui" if rapport_technique else "Non", seuil_requis="Oui"),
        QualCriterion("RAPPORT_TOURS", "Rapport tours clients OTIF", 25_000,
                      eligible=qualif and rapport_tour_clients,
                      valeur_atteinte="Oui" if rapport_tour_clients else "Non", seuil_requis="Oui"),
    ]


# ──────────────────────────────────────────────────────────
# ATC Farine (§7.2 V11 — pas de critères ferme, focusSell-In farine)
# Paliers identiques à ATC_BV. Critères qualitatifs : ventes terrain, pas KPIs ferme
# ──────────────────────────────────────────────────────────
def _calc_atc_farine(r: BonusResult, vol_real, vol_obj, mnt_fact, mnt_recouv,
                     nb_portefeuille, nb_achat, nb_croissance,
                     top_vol, top_vol_n1, nb_visites_real, nb_visites_obj,
                     planning_avant_01, taux_crm_cmd, taux_crm_vis,
                     taux_rapports, ca_nouvelles_affaires):
    r.prime_suivi_fixe = 100_000
    r.commission_nouvelles_affaires = round(ca_nouvelles_affaires * 0.005, 2)

    taux = _taux(vol_real, vol_obj)
    r.taux_atteinte_global = round(taux * 100, 2)
    r.prime_quantitative = _palier(taux, PALIERS_ATC_BV)

    qualif = taux >= 0.90
    r.qualitative_eligible = qualif

    taux_recouv  = _taux(mnt_recouv, mnt_fact) if mnt_fact > 0 else 0
    pct_achat    = _taux(nb_achat, nb_portefeuille) if nb_portefeuille > 0 else 0
    pct_crois    = _taux(nb_croissance, nb_portefeuille) if nb_portefeuille > 0 else 0
    taux_visites = _taux(nb_visites_real, nb_visites_obj) if nb_visites_obj > 0 else 0
    taux_crm     = min(taux_crm_cmd, taux_crm_vis)

    r.criteria = [
        QualCriterion("RECOUVREMENT", "Recouvrement ≥ 90%", 30_000,
                      eligible=qualif and taux_recouv >= 0.90,
                      valeur_atteinte=f"{taux_recouv*100:.1f}%", seuil_requis="90%"),
        QualCriterion("PORTEFEUILLE_ACHAT", "Ventes ≥ 70% du portefeuille", 40_000,
                      eligible=qualif and pct_achat >= 0.70,
                      valeur_atteinte=f"{pct_achat*100:.1f}%", seuil_requis="70%"),
        QualCriterion("CLIENTS_CROISSANCE", "≥ 70% clients iso/croissance vs N-1", 30_000,
                      eligible=qualif and pct_crois >= 0.70,
                      valeur_atteinte=f"{pct_crois*100:.1f}%", seuil_requis="70%"),
        QualCriterion("TOP10_CROISSANCE", "Top 10 clients farine en croissance vs N-1", 20_000,
                      eligible=qualif and top_vol >= top_vol_n1,
                      valeur_atteinte=f"{top_vol:,.0f}", seuil_requis=f"≥ {top_vol_n1:,.0f}"),
        QualCriterion("VISITES_JOURNALIERES", "100% visites journalières (15/j) + planning avant le 01", 30_000,
                      eligible=qualif and taux_visites >= 1.0 and planning_avant_01,
                      valeur_atteinte=f"{taux_visites*100:.1f}%", seuil_requis="100%"),
        QualCriterion("RAPPORTS_CRM", "Rapports activités + réclamations CRM", 50_000,
                      eligible=qualif and taux_crm >= 1.0 and taux_rapports >= 1.0,
                      valeur_atteinte=f"CRM:{taux_crm*100:.0f}% / Rapports:{taux_rapports*100:.0f}%",
                      seuil_requis="100%"),
    ]
