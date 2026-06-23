from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.employee import Employee, Region, TypePoste
from ..models.bonus import Bonus, BonusPeriod, StatutBonus
from ..models.sales import SaleData
from ..models.objective import Objective, Gamme, ClientMonthlySale, Client

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/{periode}")
def get_dashboard(periode: str, db: Session = Depends(get_db)):
    period = db.query(BonusPeriod).filter(BonusPeriod.periode == periode).first()

    bonuses = []
    if period:
        bonuses = db.query(Bonus).filter(Bonus.period_id == period.id).all()

    total_primes = sum(float(b.total) for b in bonuses)
    nb_employes = db.query(Employee).filter(Employee.actif == True).count()
    nb_calcules = len(bonuses)

    taux_moyen = (
        sum(float(b.taux_atteinte_global or 0) for b in bonuses) / nb_calcules
        if nb_calcules > 0 else 0
    )

    # CA total période
    ca_total = db.query(func.sum(SaleData.montant_ht)).filter(
        SaleData.periode == periode
    ).scalar() or 0

    # Recouvrement total
    mnt_fact = db.query(func.sum(SaleData.montant_ht)).filter(
        SaleData.periode == periode
    ).scalar() or 0
    mnt_recouv = db.query(func.sum(SaleData.montant_recouvre)).filter(
        SaleData.periode == periode
    ).scalar() or 0
    taux_recouv = (float(mnt_recouv) / float(mnt_fact) * 100) if mnt_fact > 0 else 0

    # Top performers
    top_performers = sorted(
        [
            {
                "employee_id": b.employee_id,
                "taux_atteinte": float(b.taux_atteinte_global or 0),
                "total_prime": float(b.total),
            }
            for b in bonuses
        ],
        key=lambda x: x["taux_atteinte"],
        reverse=True,
    )[:10]

    # Distribution par rôle
    by_role = {}
    for b in bonuses:
        emp = db.query(Employee).filter(Employee.id == b.employee_id).first()
        if emp:
            role = emp.type_poste.value
            if role not in by_role:
                by_role[role] = {"count": 0, "total_prime": 0, "taux_moyen": 0, "tauxes": []}
            by_role[role]["count"] += 1
            by_role[role]["total_prime"] += float(b.total)
            by_role[role]["tauxes"].append(float(b.taux_atteinte_global or 0))

    for role_data in by_role.values():
        tauxes = role_data.pop("tauxes")
        role_data["taux_moyen"] = sum(tauxes) / len(tauxes) if tauxes else 0

    # ── Ventes vs Objectifs par zone ──────────────────────
    employes_idx  = {e.id: e for e in db.query(Employee).all()}
    regions_idx   = {r.id: r for r in db.query(Region).all()}
    emp_zone      = {
        eid: (regions_idx[e.region_id].nom if e.region_id and e.region_id in regions_idx else None)
        for eid, e in employes_idx.items()
    }

    sales_by_zone: dict[str, float] = {}
    for s in db.query(SaleData).filter(SaleData.periode == periode).all():
        zone = emp_zone.get(s.employee_id)
        if zone:
            sales_by_zone[zone] = round(sales_by_zone.get(zone, 0) + float(s.volume or 0), 1)

    # Objectifs par zone : on somme tous les gammes sauf ALL (éviter double-comptage)
    obj_by_zone: dict[str, float] = {}
    for o in db.query(Objective).filter(
        Objective.periode == periode,
        Objective.gamme != Gamme.ALL,
    ).all():
        zone = emp_zone.get(o.employee_id)
        if zone:
            obj_by_zone[zone] = round(obj_by_zone.get(zone, 0) + float(o.objectif_volume or 0), 1)

    zones_order = ["DAKAR", "NORD", "CENTRE", "SUD", "EXPORT"]
    all_zones   = sorted(
        set(list(sales_by_zone.keys()) + list(obj_by_zone.keys())),
        key=lambda z: zones_order.index(z) if z in zones_order else 99,
    )
    by_zone = [
        {
            "zone":     z,
            "realise":  round(sales_by_zone.get(z, 0), 1),
            "objectif": round(obj_by_zone.get(z, 0), 1),
        }
        for z in all_zones
    ]

    # ── Ventes par gamme ───────────────────────────────────
    raw_gamme = (
        db.query(SaleData.gamme, func.sum(SaleData.volume).label("tonnage"))
        .filter(SaleData.periode == periode)
        .group_by(SaleData.gamme)
        .all()
    )
    by_gamme = [
        {
            "gamme":   str(row.gamme.value if hasattr(row.gamme, "value") else row.gamme),
            "tonnage": round(float(row.tonnage or 0), 1),
        }
        for row in raw_gamme
        if float(row.tonnage or 0) > 0
    ]
    by_gamme.sort(key=lambda x: x["tonnage"], reverse=True)

    return {
        "periode": periode,
        "statut_periode": period.statut.value if period else "NON_CALCULE",
        "kpis": {
            "nb_employes": nb_employes,
            "nb_calcules": nb_calcules,
            "total_primes_fcfa": total_primes,
            "taux_atteinte_moyen": round(taux_moyen, 1),
            "ca_total_fcfa": float(ca_total),
            "taux_recouvrement": round(taux_recouv, 1),
        },
        "top_performers": top_performers,
        "by_role": by_role,
        "by_zone": by_zone,
        "by_gamme": by_gamme,
    }


@router.get("/ventes")
def get_ventes(
    periode: Optional[str] = Query(None),
    region_id: Optional[int] = Query(None),
    gamme: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Ventes agrégées par commercial — tableau style Power BI."""
    q = db.query(SaleData)
    if periode:
        q = q.filter(SaleData.periode == periode)
    if gamme:
        q = q.filter(SaleData.gamme == gamme)

    sales = q.all()

    # Index employés et régions
    employes  = {e.id: e for e in db.query(Employee).all()}
    regions   = {r.id: r for r in db.query(Region).all()}

    # Objectifs de la période (tous les gammes ou filtré)
    obj_q = db.query(Objective).filter(Objective.periode == periode) if periode else db.query(Objective)
    if gamme:
        obj_q = obj_q.filter(Objective.gamme == gamme)
    # objectif total par employé (somme des gammes ou gamme filtrée)
    obj_par_emp: dict[int, float] = {}
    for o in obj_q.all():
        obj_par_emp[o.employee_id] = obj_par_emp.get(o.employee_id, 0) + float(o.objectif_volume or 0)

    # Agrégation par employé
    agg: dict[int, dict] = {}
    gammes_presentes: set = set()

    for s in sales:
        emp = employes.get(s.employee_id)
        if not emp:
            continue
        if region_id and emp.region_id != region_id:
            continue

        eid = emp.id
        if eid not in agg:
            region = regions.get(emp.region_id)
            agg[eid] = {
                "employee_id":    eid,
                "nom":            f"{emp.prenom} {emp.nom}",
                "zone":           region.nom if region else "—",
                "type_poste":     emp.type_poste.value,
                "tonnage":        0.0,
                "objectif":       obj_par_emp.get(eid, 0.0),
                "ca_facture":     0.0,
                "ca_recouvre":    0.0,
                "par_gamme":      {},
            }
        agg[eid]["tonnage"]     += float(s.volume or 0)
        agg[eid]["ca_facture"]  += float(s.montant_ht or 0)
        agg[eid]["ca_recouvre"] += float(s.montant_recouvre or 0)

        g = s.gamme.value if hasattr(s.gamme, "value") else str(s.gamme)
        gammes_presentes.add(g)
        pg = agg[eid]["par_gamme"]
        if g not in pg:
            pg[g] = {"tonnage": 0.0, "ca_facture": 0.0}
        pg[g]["tonnage"]    += float(s.volume or 0)
        pg[g]["ca_facture"] += float(s.montant_ht or 0)

    rows = sorted(agg.values(), key=lambda x: x["nom"])

    # Totaux
    total_tonnage    = sum(r["tonnage"]     for r in rows)
    total_ca_facture = sum(r["ca_facture"]  for r in rows)
    total_ca_recouv  = sum(r["ca_recouvre"] for r in rows)

    # Répartition tonnage par gamme (pour graphique camembert)
    tonnage_par_gamme: dict[str, float] = {}
    for r in rows:
        for g, d in r["par_gamme"].items():
            tonnage_par_gamme[g] = tonnage_par_gamme.get(g, 0) + d["tonnage"]

    return {
        "rows": rows,
        "totaux": {
            "tonnage":     round(total_tonnage, 1),
            "ca_facture":  round(total_ca_facture, 0),
            "ca_recouvre": round(total_ca_recouv, 0),
            "tx_recouvrement": round(
                total_ca_recouv / total_ca_facture * 100 if total_ca_facture else 0, 1
            ),
        },
        "tonnage_par_gamme": {k: round(v, 1) for k, v in tonnage_par_gamme.items()},
        "gammes": sorted(gammes_presentes),
    }


@router.get("/ventes/clients")
def get_ventes_clients(
    periode: str = Query(...),
    employee_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Détail par client pour un commercial donné sur une période."""
    from datetime import date
    from dateutil.relativedelta import relativedelta

    # Calcul bornes nouvelles affaires : ouverture entre (M-1 - 12 mois) et fin M-1
    annee, mois = int(periode[:4]), int(periode[5:7])
    debut_m  = date(annee, mois, 1)
    debut_m1 = debut_m - relativedelta(months=1)
    date_limite_new = debut_m1 - relativedelta(months=12)

    # Index date_ouverture par code_sap
    clients_db = db.query(Client).all()
    date_ouverture: dict[str, date | None] = {c.code_sap: c.date_ouverture for c in clients_db}

    rows = (
        db.query(ClientMonthlySale)
        .filter(
            ClientMonthlySale.employee_id == employee_id,
            ClientMonthlySale.periode == periode,
            ClientMonthlySale.annee_n1 == False,
        )
        .order_by(ClientMonthlySale.montant_ca.desc())
        .all()
    )

    data = []
    for r in rows:
        do = date_ouverture.get(r.client_code)
        is_new = bool(do and date_limite_new <= do < debut_m)
        data.append({
            "client_code":          r.client_code,
            "client_nom":           r.client_nom or r.client_code,
            "montant_ca":           round(float(r.montant_ca or 0), 0),
            "montant_recouvre":     round(float(r.montant_recouvre or 0), 0),
            "is_nouvelle_affaire":  is_new,
        })

    total_ca  = sum(d["montant_ca"]       for d in data)
    total_rec = sum(d["montant_recouvre"] for d in data)

    return {
        "clients": data,
        "totaux": {
            "montant_ca":       round(total_ca, 0),
            "montant_recouvre": round(total_rec, 0),
            "tx_recouvrement":  round(total_rec / total_ca * 100 if total_ca else 0, 1),
            "nb_nouvelles":     sum(1 for d in data if d["is_nouvelle_affaire"]),
        },
    }
