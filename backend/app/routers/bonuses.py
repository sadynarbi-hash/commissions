from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
import io

from ..database import get_db
from ..models.employee import Employee
from ..models.bonus import Bonus, BonusQualDetail, BonusPeriod, StatutBonus
from ..models.objective import Objective, Gamme, SalesForecast, ClientPortfolio, Client, ClientMonthlySale
from ..models.geography import Secteur
from ..models.sales import SaleData
from ..models.visit import VisitData, ManualCriteria
from ..schemas.bonus import (
    BonusRead, BonusPeriodRead, BonusCalculateRequest,
    BonusValidateRequest, ManualCriteriaInput,
)
from ..services.bonus_engine import calculate_bonus

router = APIRouter(prefix="/api", tags=["bonuses"])


def _build_bonus_inputs(employee: Employee, periode: str, db: Session) -> dict:
    """Agrège toutes les données nécessaires pour calculer la prime d'un employé."""
    from collections import defaultdict
    from ..models.employee import TypePoste as _TP

    annee = int(periode[:4])
    annee_n1 = annee - 1

    # ── Source des données de volume ───────────────────────────────────────────
    # RCR et SV : leurs taux sont calculés sur les réalisations agrégées de leurs
    # collaborateurs (COMMERCIAL + ATC_BV + ATC_FARINE) dans la même région.
    # Tous les autres rôles : leurs propres données.
    _COLLAB_TYPES = (_TP.COMMERCIAL, _TP.ATC_BV, _TP.ATC_FARINE)
    if employee.type_poste in (_TP.RCR, _TP.SV) and employee.region_id:
        collabs_all = db.query(Employee).filter(
            Employee.region_id == employee.region_id,
            Employee.type_poste.in_(_COLLAB_TYPES),
        ).all()
        # Réalisé : inclure les inactifs (leurs ventes passées comptent)
        source_ids = [e.id for e in collabs_all] or [employee.id]
        # Objectif : seulement les actifs (un inactif n'a plus d'objectif à atteindre)
        source_ids_obj = [e.id for e in collabs_all if e.actif] or source_ids
    elif employee.type_poste == _TP.RESP_TECH_FP:
        # RESP_TECH_FP : objectif national FARINE + PÂTES — agrège tous les commerciaux/ATC
        fp_emps = db.query(Employee).filter(
            Employee.type_poste.in_((_TP.COMMERCIAL, _TP.ATC_FARINE)),
        ).all()
        source_ids     = [e.id for e in fp_emps] or [employee.id]
        source_ids_obj = [e.id for e in fp_emps if e.actif] or source_ids
    else:
        source_ids = [employee.id]
        source_ids_obj = [employee.id]

    # ── Objectifs ──────────────────────────────────────────
    objs = db.query(Objective).filter(
        Objective.employee_id.in_(source_ids_obj),
        Objective.periode == periode,
    ).all()
    obj_sums: dict = defaultdict(float)
    for o in objs:
        obj_sums[o.gamme] += float(o.objectif_volume or 0)

    def get_obj_volume(gamme: Gamme) -> float:
        return obj_sums.get(gamme, 0.0)

    obj_all    = get_obj_volume(Gamme.ALL)
    obj_pates  = get_obj_volume(Gamme.PATES)
    obj_farine = get_obj_volume(Gamme.FARINE)
    obj_nutri  = get_obj_volume(Gamme.NUTRITION_ANIMALE)
    # BVF peut être stocké agrégé (BVF) ou séparé (BETAIL + VOLAILLE selon le seeder)
    obj_bvf    = get_obj_volume(Gamme.BVF) or (
                     get_obj_volume(Gamme.BETAIL) + get_obj_volume(Gamme.VOLAILLE)
                 )

    # ── Ventes réelles (mois M) ────────────────────────────
    sales = db.query(SaleData).filter(
        SaleData.employee_id.in_(source_ids),
        SaleData.periode == periode,
    ).all()

    vol_total = sum(float(s.volume) for s in sales)
    vol_pates = sum(float(s.volume) for s in sales if s.gamme == Gamme.PATES)
    vol_autres = vol_total - vol_pates
    mnt_facture = sum(float(s.montant_ht) for s in sales)

    # SV fallback : si les objectifs par gamme sont absents mais obj_all existe,
    # répartir obj_all proportionnellement au réalisé pâtes/autres.
    if (employee.type_poste == _TP.SV
            and obj_pates == 0 and obj_bvf == 0 and obj_farine == 0
            and obj_all > 0 and vol_total > 0):
        ratio_pates = vol_pates / vol_total
        obj_pates   = obj_all * ratio_pates
        obj_bvf     = obj_all * (1 - ratio_pates)

    # ── Recouvrement M-1 (règle métier NMA) ───────────────
    # Le taux de recouvrement du bonus de mois M = MontantPayé(M-1) / CA(M-1)
    annee_i, mois_i = int(periode[:4]), int(periode[5:7])
    periode_m1 = f"{annee_i - 1}-12" if mois_i == 1 else f"{annee_i}-{mois_i - 1:02d}"
    sales_m1 = db.query(SaleData).filter(
        SaleData.employee_id.in_(source_ids),
        SaleData.periode     == periode_m1,
    ).all()
    mnt_facture_m1 = sum(float(s.montant_ht) for s in sales_m1)
    mnt_recouv     = sum(float(s.montant_recouvre) for s in sales_m1)

    # ── Prévisions (pour taux de précision) ────────────────
    forecasts = db.query(SalesForecast).filter(
        SalesForecast.employee_id.in_(source_ids),
        SalesForecast.periode == periode,
        SalesForecast.gamme == Gamme.ALL,
    ).all()
    prevision = sum(float(f.volume_prevu or 0) for f in forecasts)

    # ── Portefeuille via secteurs ──────────────────────────
    # Portfolio = clients dont u_secteur correspond à un secteur assigné au(x) commercial(aux).
    secteur_codes = [
        s.code for s in
        db.query(Secteur).filter(Secteur.employee_id.in_(source_ids)).all()
    ]
    if secteur_codes:
        portfolio_clients = db.query(Client.code_sap).filter(
            Client.u_secteur.in_(secteur_codes)
        ).all()
        portfolio_codes = {row.code_sap for row in portfolio_clients}
    else:
        # Fallback : ancienne méthode ClientPortfolio si secteurs pas encore seedés
        portfolio_clients = (
            db.query(Client.code_sap)
            .join(ClientPortfolio, ClientPortfolio.client_id == Client.id)
            .filter(ClientPortfolio.employee_id.in_(source_ids),
                    ClientPortfolio.annee == annee)
            .all()
        )
        portfolio_codes = {row.code_sap for row in portfolio_clients}
    nb_portefeuille = len(portfolio_codes)

    # Volumes courants par client (depuis ClientMonthlySale) — agrégés si plusieurs sources
    cms_courant = db.query(ClientMonthlySale).filter(
        ClientMonthlySale.employee_id.in_(source_ids),
        ClientMonthlySale.periode     == periode,
        ClientMonthlySale.annee_n1    == False,
    ).all()
    vol_by_client: dict[str, float] = defaultdict(float)
    for c in cms_courant:
        vol_by_client[c.client_code] += float(c.volume)

    # Volumes N-1 (même mois, année précédente)
    periode_n1 = f"{annee - 1}-{periode[5:]}"
    cms_n1 = db.query(ClientMonthlySale).filter(
        ClientMonthlySale.employee_id.in_(source_ids),
        ClientMonthlySale.periode     == periode_n1,
        ClientMonthlySale.annee_n1    == True,
    ).all()
    vol_n1_by_client: dict[str, float] = defaultdict(float)
    for c in cms_n1:
        vol_n1_by_client[c.client_code] += float(c.volume)

    # Clients du portefeuille ayant acheté ce mois
    nb_achat = sum(1 for code in portfolio_codes if vol_by_client.get(code, 0) > 0)

    # Clients iso/croissance vs N-1
    nb_croissance = sum(
        1 for code in portfolio_codes
        if vol_by_client.get(code, 0) >= vol_n1_by_client.get(code, 0)
    )
    nb_actifs = nb_achat

    # Top clients par volume courant
    sorted_clients = sorted(vol_by_client.items(), key=lambda x: x[1], reverse=True)
    top10_vol    = sum(v for _, v in sorted_clients[:10])
    top10_vol_n1 = sum(vol_n1_by_client.get(c, 0) for c, _ in sorted_clients[:10])
    top15_vol    = sum(v for _, v in sorted_clients[:15])
    top15_vol_n1 = sum(vol_n1_by_client.get(c, 0) for c, _ in sorted_clients[:15])
    top5_vol     = sum(v for _, v in sorted_clients[:5])
    top5_vol_n1  = sum(vol_n1_by_client.get(c, 0) for c, _ in sorted_clients[:5])

    # Choix du top N selon le rôle (RCR=15, RCE=5, autres=10)
    if employee.type_poste == _TP.RCR:
        top_vol_ret, top_vol_n1_ret = top15_vol, top15_vol_n1
    elif employee.type_poste == _TP.RCE:
        top_vol_ret, top_vol_n1_ret = top5_vol, top5_vol_n1
    else:
        top_vol_ret, top_vol_n1_ret = top10_vol, top10_vol_n1

    # ── Visites (Salesforce) — agrégées depuis les commerciaux sources ─────────
    visits = db.query(VisitData).filter(
        VisitData.employee_id.in_(source_ids),
        VisitData.periode == periode,
    ).all()
    nb_visites = len(visits)
    nb_fermes = sum(1 for v in visits if v.type_visite.value == "FERME")

    from calendar import monthrange
    jours_ouvres = 22
    nb_fermes_par_jour_moy = nb_fermes / jours_ouvres if nb_fermes > 0 else 0.0

    # Objectif visites COMMERCIAL : 20/j pâtes, 15/j BV (document V11 §7.1)
    secteurs_emp = db.query(Secteur).filter(Secteur.employee_id.in_(source_ids)).all()
    gammes_emp   = {(s.gamme or "").upper() for s in secteurs_emp}
    est_pates    = any("PAT" in g or "FAR" in g for g in gammes_emp)
    visites_par_jour = 20 if est_pates else 15
    nb_visites_objectif = jours_ouvres * visites_par_jour * len(source_ids)

    taux_crm_vis = sum(1 for v in visits if v.visite_saisie_crm) / nb_visites if nb_visites > 0 else 0.0
    taux_crm_cmd = sum(1 for v in visits if v.commande_saisie) / nb_visites if nb_visites > 0 else 0.0
    taux_kpis = sum(1 for v in visits if v.kpis_json) / nb_visites if nb_visites > 0 else 0.0

    # ── Critères manuels — toujours depuis le manager lui-même ────────────────
    def get_manual(code: str) -> bool:
        mc = db.query(ManualCriteria).filter(
            ManualCriteria.employee_id == employee.id,
            ManualCriteria.periode == periode,
            ManualCriteria.critere_code == code,
        ).first()
        return mc.valeur if mc else False

    # ── Fallbacks manuels (quand Salesforce non disponible) ──────────────────
    if nb_visites == 0:
        if get_manual("VISITES_JOURNALIERES") or get_manual("VISITES_FERMES"):
            nb_visites = nb_visites_objectif
        if get_manual("CRM_CONFORMITE"):
            taux_crm_cmd = 1.0
            taux_crm_vis = 1.0
        if get_manual("KPIS_FERME"):
            taux_kpis = 1.0
    if prevision == 0.0 and get_manual("PREVISION"):
        prevision = vol_total  # ratio = 1.0 si vol_total > 0

    # ── Nouvelles affaires ─────────────────────────────────
    # Commission = 0.5% × CA recouvré M-1 des clients dont le compte a été ouvert
    # dans les 12 mois précédant la période M-1.
    from datetime import date as _date
    from calendar import monthrange as _mr_na
    annee_m1_i, mois_m1_i = int(periode_m1[:4]), int(periode_m1[5:7])
    # Date limite : un client est "nouveau" si OCRD.CreateDate >= M-1 - 12 mois
    if mois_m1_i == 1:
        date_limite_new = _date(annee_m1_i - 1, 1, 1)
    else:
        date_limite_new = _date(annee_m1_i - 1, mois_m1_i, 1)

    new_client_codes: set[str] = set()
    if portfolio_codes:
        new_clients_q = db.query(Client.code_sap).filter(
            Client.code_sap.in_(portfolio_codes),
            Client.date_ouverture.isnot(None),
            Client.date_ouverture >= date_limite_new,
        ).all()
        new_client_codes = {row.code_sap for row in new_clients_q}

    ca_new_m          = 0.0
    ca_new_m_recouvre = 0.0
    if new_client_codes:
        row = db.query(
            func.sum(ClientMonthlySale.montant_ca),
            func.sum(ClientMonthlySale.montant_recouvre),
        ).filter(
            ClientMonthlySale.employee_id.in_(source_ids),
            ClientMonthlySale.periode == periode,   # M (mois courant)
            ClientMonthlySale.client_code.in_(new_client_codes),
            ClientMonthlySale.annee_n1 == False,
        ).one()
        ca_new_m          = float(row[0] or 0)
        ca_new_m_recouvre = float(row[1] or 0)

    taux_recouv_m1_f = mnt_recouv / mnt_facture_m1 if mnt_facture_m1 > 0 else 0.0
    # CA nouveaux clients du mois M × taux recouvrement M-1
    # (les clients achètent à crédit : on applique le taux de recouvrement du mois précédent)
    if ca_new_m_recouvre > 0:
        ca_nouvelles = ca_new_m_recouvre
    else:
        ca_nouvelles = ca_new_m * taux_recouv_m1_f

    # RESP_TECH_FP : taux calculé sur FARINE + PÂTES uniquement (scope national)
    if employee.type_poste == _TP.RESP_TECH_FP:
        vol_fp        = sum(float(s.volume) for s in sales if s.gamme in (Gamme.FARINE, Gamme.PATES))
        obj_fp        = obj_pates + obj_farine
        _vol_realise  = vol_fp
        _vol_objectif = obj_fp
    else:
        _vol_realise  = vol_total
        _vol_objectif = obj_all or (obj_bvf + obj_pates + obj_farine)

    return dict(
        employee_id=employee.id,
        type_poste=employee.type_poste,
        periode=periode,
        volume_realise=_vol_realise,
        volume_objectif=_vol_objectif,
        volume_pates_realise=vol_pates,
        volume_pates_objectif=obj_pates,
        volume_autres_realise=vol_autres,
        volume_autres_objectif=obj_bvf + obj_farine + obj_nutri,
        montant_facture=mnt_facture_m1,    # M-1 : base recouvrement
        montant_recouvre=mnt_recouv,       # M-1 : montant récupéré
        montant_facture_m=mnt_facture,     # M   : base prime quantitative V12
        prevision=prevision,
        realise_pour_prevision=vol_total,
        nb_clients_portefeuille=nb_portefeuille,
        nb_clients_avec_achat=nb_achat,
        nb_clients_visite=len(set(v.client_code for v in visits if v.client_code)),
        nb_clients_croissance=nb_croissance,
        nb_clients_actifs=nb_actifs,
        top_clients_volume=top_vol_ret,
        top_clients_volume_n1=top_vol_n1_ret,
        nb_visites_realisees=nb_visites,
        nb_visites_objectif=nb_visites_objectif,
        nb_fermes_par_jour_moy=nb_fermes_par_jour_moy,
        taux_crm_commandes=taux_crm_cmd,
        taux_crm_visites=taux_crm_vis,
        taux_rapport_activities=get_manual("RAPPORTS_ENVOYES") and 1.0 or 0.0,
        taux_kpis_ferme=taux_kpis,
        planning_envoye_avant_01=get_manual("PLANNING_AVANT_01"),
        rapport_technique_envoye=get_manual("RAPPORT_TECHNIQUE"),
        rapport_tour_clients=get_manual("RAPPORT_TOURS"),
        reclamations_traitees_otif=get_manual("RECLAMATIONS_OTIF"),
        accompagnement_managerial=get_manual("ACCOMPAGNEMENT"),
        ca_nouvelles_affaires=ca_nouvelles,
    )


@router.get("/bonus-periods", response_model=List[BonusPeriodRead])
def list_periods(db: Session = Depends(get_db)):
    return db.query(BonusPeriod).order_by(BonusPeriod.periode.desc()).all()


@router.post("/bonuses/calculate", status_code=200)
def calculate_bonuses(body: BonusCalculateRequest, db: Session = Depends(get_db)):
    """Lance le calcul des primes pour une période."""
    period = db.query(BonusPeriod).filter(BonusPeriod.periode == body.periode).first()
    if not period:
        period = BonusPeriod(periode=body.periode)
        db.add(period)
        db.flush()

    q = db.query(Employee).filter(Employee.actif == True)
    if body.employee_ids:
        q = q.filter(Employee.id.in_(body.employee_ids))
    employees = q.all()

    results = []
    for emp in employees:
        try:
            inputs = _build_bonus_inputs(emp, body.periode, db)
            bonus_result = calculate_bonus(**inputs)

            existing = db.query(Bonus).filter(
                Bonus.employee_id == emp.id,
                Bonus.period_id == period.id,
            ).first()
            if existing:
                db.query(BonusQualDetail).filter(BonusQualDetail.bonus_id == existing.id).delete()
                bonus_rec = existing
            else:
                bonus_rec = Bonus(employee_id=emp.id, period_id=period.id)
                db.add(bonus_rec)
                db.flush()

            bonus_rec.volume_realise = inputs.get("volume_realise", 0)
            bonus_rec.volume_objectif = inputs.get("volume_objectif", 0)
            bonus_rec.nb_visites = inputs.get("nb_visites_realisees", 0)
            bonus_rec.taux_atteinte_global = bonus_result.taux_atteinte_global
            bonus_rec.taux_atteinte_pates = bonus_result.taux_atteinte_pates
            bonus_rec.taux_atteinte_autres = bonus_result.taux_atteinte_autres
            bonus_rec.prime_suivi_fixe = bonus_result.prime_suivi_fixe
            bonus_rec.prime_quantitative = bonus_result.prime_quantitative
            bonus_rec.prime_qualitative = bonus_result.prime_qualitative
            bonus_rec.commission_nouvelles_affaires = bonus_result.commission_nouvelles_affaires
            bonus_rec.total = bonus_result.total
            bonus_rec.qualitative_eligible = bonus_result.qualitative_eligible
            bonus_rec.detail_json = bonus_result.to_detail_dict()
            bonus_rec.statut = StatutBonus.CALCULE
            bonus_rec.calcule_le = datetime.utcnow()

            for c in bonus_result.criteria:
                detail = BonusQualDetail(
                    bonus_id=bonus_rec.id,
                    critere_code=c.code,
                    critere_libelle=c.libelle,
                    valeur_atteinte=c.valeur_atteinte,
                    seuil_requis=c.seuil_requis,
                    montant_max=c.montant_max,
                    montant_accorde=c.montant_accorde,
                    eligible=c.eligible,
                )
                db.add(detail)

            results.append({"employee_id": emp.id, "total": bonus_result.total, "statut": "ok"})
        except Exception as e:
            results.append({"employee_id": emp.id, "statut": "erreur", "message": str(e)})

    period.date_calcul = datetime.utcnow()
    period.statut = StatutBonus.CALCULE
    db.commit()
    return {"periode": body.periode, "nb_calcules": len(results), "details": results}


@router.get("/bonuses", response_model=List[BonusRead])
def list_bonuses(
    periode: Optional[str] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Bonus).join(Employee).filter(Employee.actif == True)
    if periode:
        q = q.join(BonusPeriod).filter(BonusPeriod.periode == periode)
    if employee_id:
        q = q.filter(Bonus.employee_id == employee_id)
    return q.all()


@router.get("/bonuses/{bonus_id}", response_model=BonusRead)
def get_bonus(bonus_id: int, db: Session = Depends(get_db)):
    b = db.query(Bonus).filter(Bonus.id == bonus_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Prime introuvable")
    return b


@router.post("/bonuses/validate")
def validate_bonuses(body: BonusValidateRequest, db: Session = Depends(get_db)):
    period = db.query(BonusPeriod).filter(BonusPeriod.periode == body.periode).first()
    if not period:
        raise HTTPException(status_code=404, detail="Période introuvable")
    period.statut = StatutBonus.VALIDE
    period.valide_par = body.valide_par
    period.date_validation = datetime.utcnow()
    db.query(Bonus).filter(Bonus.period_id == period.id).update(
        {"statut": StatutBonus.VALIDE}
    )
    db.commit()
    return {"detail": "Primes validées", "periode": body.periode}


@router.get("/manual-criteria")
def list_manual_criteria(periode: str, db: Session = Depends(get_db)):
    criteria = db.query(ManualCriteria).filter(ManualCriteria.periode == periode).all()
    return [
        {
            "employee_id": mc.employee_id,
            "critere_code": mc.critere_code,
            "valeur": mc.valeur,
            "saisi_par": mc.saisi_par,
        }
        for mc in criteria
    ]


@router.post("/manual-criteria", status_code=201)
def upsert_manual_criteria(body: ManualCriteriaInput, db: Session = Depends(get_db)):
    mc = db.query(ManualCriteria).filter(
        ManualCriteria.employee_id == body.employee_id,
        ManualCriteria.periode == body.periode,
        ManualCriteria.critere_code == body.critere_code,
    ).first()
    if mc:
        mc.valeur = body.valeur
        mc.notes = body.notes
        mc.saisi_par = body.saisi_par
    else:
        mc = ManualCriteria(**body.model_dump())
        db.add(mc)
    db.commit()
    return {"detail": "sauvegardé"}


@router.get("/bonuses/{bonus_id}/pv")
def download_pv(bonus_id: int, db: Session = Depends(get_db)):
    """Génère le PV de commission PDF pour un bonus."""
    import traceback
    from ..services.pv_pdf import generate_pv_pdf
    b = db.query(Bonus).filter(Bonus.id == bonus_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Prime introuvable")
    emp = db.query(Employee).filter(Employee.id == b.employee_id).first()
    region_nom = emp.region.nom if emp and emp.region else ""
    period_obj = db.query(BonusPeriod).filter(BonusPeriod.id == b.period_id).first()
    periode_str = period_obj.periode if period_obj else ""
    try:
        pdf_bytes = generate_pv_pdf(b, emp, region_nom, periode_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur PDF: {traceback.format_exc()}")
    nom = f"{emp.prenom}_{emp.nom}".replace(" ", "_") if emp else str(bonus_id)
    filename = f"PV_commission_{nom}_{periode_str}.pdf"
    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )


@router.get("/bonuses/recap/{periode}")
def download_recap(periode: str, db: Session = Depends(get_db)):
    """Récapitulatif mensuel PDF de toutes les commissions — pour les RH."""
    from ..services.recap_pdf import generate_recap_pdf
    from fastapi.responses import Response

    period = db.query(BonusPeriod).filter(BonusPeriod.periode == periode).first()
    if not period:
        raise HTTPException(status_code=404, detail="Période introuvable")

    bonuses = db.query(Bonus).join(Employee).filter(
        Bonus.period_id == period.id,
        Employee.actif == True,
    ).all()
    rows = []
    for b in bonuses:
        emp = db.query(Employee).filter(Employee.id == b.employee_id).first()
        if not emp:
            continue
        rows.append({
            "nom":                          emp.nom,
            "prenom":                       emp.prenom,
            "role":                         emp.type_poste.value if hasattr(emp.type_poste, "value") else str(emp.type_poste),
            "region":                       emp.region.nom if emp.region else "—",
            "prime_suivi_fixe":             float(b.prime_suivi_fixe),
            "prime_quantitative":           float(b.prime_quantitative),
            "prime_qualitative":            float(b.prime_qualitative),
            "commission_nouvelles_affaires": float(b.commission_nouvelles_affaires),
            "total":                        float(b.total),
        })

    pdf_bytes = generate_recap_pdf(rows, periode)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"recap_commissions_{periode}.pdf\""},
    )


@router.get("/bonuses/export-detail/{periode}")
def export_bonuses_detail(periode: str, db: Session = Depends(get_db)):
    """Export Excel détaillé : quanti par gamme + quali par critère, filtrable par rôle."""
    from ..services.export_excel_detail import generate_detail_excel
    try:
        xlsx_bytes = generate_detail_excel(db, periode)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=primes_detail_{periode}.xlsx"},
    )


@router.get("/bonuses/export/{periode}")
def export_bonuses(periode: str, db: Session = Depends(get_db)):
    """Export Excel de toutes les primes d'une période."""
    import pandas as pd

    period = db.query(BonusPeriod).filter(BonusPeriod.periode == periode).first()
    if not period:
        raise HTTPException(status_code=404, detail="Période introuvable")

    bonuses = db.query(Bonus).filter(Bonus.period_id == period.id).all()
    rows = []
    for b in bonuses:
        emp = db.query(Employee).filter(Employee.id == b.employee_id).first()
        rows.append({
            "Nom": f"{emp.prenom} {emp.nom}" if emp else b.employee_id,
            "Rôle": emp.type_poste.value if emp else "",
            "Région": emp.region.nom if emp and emp.region else "",
            "Taux atteinte (%)": b.taux_atteinte_global,
            "Prime fixe": b.prime_suivi_fixe,
            "Prime quantitative": b.prime_quantitative,
            "Prime qualitative": b.prime_qualitative,
            "Commission": b.commission_nouvelles_affaires,
            "TOTAL PRIME": b.total,
            "Statut": b.statut.value,
        })

    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=f"Primes {periode}")
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=primes_{periode}.xlsx"},
    )
