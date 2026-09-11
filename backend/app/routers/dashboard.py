from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.employee import Employee, Region, TypePoste
from ..models.bonus import Bonus, BonusPeriod, StatutBonus
from ..models.sales import SaleData
from ..models.objective import Objective, Gamme, ClientMonthlySale, Client, ClientPortfolio

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

    # Objectifs de la période — TOUTES gammes (pour breakdown par gamme)
    obj_q_all = db.query(Objective).filter(Objective.periode == periode) if periode else db.query(Objective)
    obj_par_emp: dict[int, float] = {}
    obj_par_emp_gamme: dict[int, dict[str, float]] = {}
    for o in obj_q_all.all():
        g_val = o.gamme.value if hasattr(o.gamme, "value") else str(o.gamme)
        vol   = float(o.objectif_volume or 0)
        # Total par employé (avec filtre gamme si actif)
        if not gamme or g_val == gamme:
            obj_par_emp[o.employee_id] = obj_par_emp.get(o.employee_id, 0) + vol
        # Par gamme (toujours sans filtre pour le drill-down)
        if o.employee_id not in obj_par_emp_gamme:
            obj_par_emp_gamme[o.employee_id] = {}
        obj_par_emp_gamme[o.employee_id][g_val] = obj_par_emp_gamme[o.employee_id].get(g_val, 0) + vol

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
                "obj_par_gamme":  obj_par_emp_gamme.get(eid, {}),
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


@router.get("/suivi-compte")
def get_suivi_compte(
    periode: str = Query(...),
    db: Session = Depends(get_db),
):
    """Tableaux de bord chargé de compte : rankings recouvrement & conversion, clients inactifs."""
    annee = int(periode[:4])

    employes = {e.id: e for e in db.query(Employee).all()}
    regions  = {r.id: r for r in db.query(Region).all()}

    # ── 1. Recouvrement + volumes par gamme depuis SaleData (période M) ────────
    sales = (
        db.query(SaleData)
        .filter(SaleData.periode == periode, SaleData.annee_n1 == False)  # noqa: E712
        .all()
    )
    rec_agg: dict[int, dict] = {}
    # vol_gamme[eid][gamme_str] = volume réalisé
    vol_gamme: dict[int, dict[str, float]] = {}

    for s in sales:
        emp = employes.get(s.employee_id)
        if not emp:
            continue
        eid = emp.id
        if eid not in rec_agg:
            reg = regions.get(emp.region_id)
            rec_agg[eid] = {
                "employee_id": eid,
                "nom":         f"{emp.prenom} {emp.nom}",
                "zone":        reg.nom if reg else "—",
                "type_poste":  emp.type_poste.value,
                "ca_facture":  0.0,
                "ca_recouvre": 0.0,
            }
        rec_agg[eid]["ca_facture"]  += float(s.montant_ht or 0)
        rec_agg[eid]["ca_recouvre"] += float(s.montant_recouvre or 0)
        g = s.gamme.value if hasattr(s.gamme, "value") else str(s.gamme)
        vol_gamme.setdefault(eid, {})
        vol_gamme[eid][g] = vol_gamme[eid].get(g, 0.0) + float(s.volume or 0)

    for r in rec_agg.values():
        r["taux_recouvrement"] = (
            round(r["ca_recouvre"] / r["ca_facture"] * 100, 1)
            if r["ca_facture"] > 0 else 0.0
        )

    # ── 1b. Objectifs par gamme (période M) ──────────────────────────────────
    obj_gamme: dict[int, dict[str, float]] = {}
    for o in db.query(Objective).filter(Objective.periode == periode).all():
        g = o.gamme.value if hasattr(o.gamme, "value") else str(o.gamme)
        obj_gamme.setdefault(o.employee_id, {})
        obj_gamme[o.employee_id][g] = obj_gamme[o.employee_id].get(g, 0.0) + float(o.objectif_volume or 0)

    # ── 1c. Classement par gamme ──────────────────────────────────────────────
    GAMMES_SUIVI = ["VOLAILLE", "FARINE", "PATES", "BETAIL"]
    ranking_gamme: dict[str, list] = {}
    for g in GAMMES_SUIVI:
        entries = []
        for eid, emp in employes.items():
            obj  = obj_gamme.get(eid, {}).get(g, 0.0)
            real = vol_gamme.get(eid, {}).get(g, 0.0)
            if obj == 0 and real == 0:
                continue
            reg = regions.get(emp.region_id)
            taux = round(real / obj * 100, 1) if obj > 0 else None
            entries.append({
                "employee_id": eid,
                "nom":         f"{emp.prenom} {emp.nom}",
                "zone":        reg.nom if reg else "—",
                "objectif":    round(obj, 1),
                "realise":     round(real, 1),
                "taux":        taux,
            })
        # Trier : ceux avec objectif d'abord (par taux desc), puis sans objectif (par réalisé desc)
        entries.sort(key=lambda x: (x["taux"] is None, -(x["taux"] or 0), -x["realise"]))
        for i, e in enumerate(entries):
            e["rang"] = i + 1
        ranking_gamme[g] = entries

    # ── 2. Clients actifs depuis ClientMonthlySale (période M) ───────────────
    client_sales = (
        db.query(ClientMonthlySale)
        .filter(ClientMonthlySale.periode == periode, ClientMonthlySale.annee_n1 == False)  # noqa: E712
        .all()
    )
    actifs: dict[int, set] = {}
    for cs in client_sales:
        if float(cs.montant_ca or 0) > 0:
            actifs.setdefault(cs.employee_id, set()).add(cs.client_code)

    # ── 3. Portefeuille depuis ClientPortfolio (année) ───────────────────────
    portfolios = (
        db.query(ClientPortfolio)
        .filter(ClientPortfolio.annee == annee)
        .all()
    )
    portefeuille: dict[int, int] = {}
    for p in portfolios:
        portefeuille[p.employee_id] = portefeuille.get(p.employee_id, 0) + 1

    # ── 4. Fusion ─────────────────────────────────────────────────────────────
    all_eids = set(rec_agg.keys()) | set(actifs.keys()) | set(portefeuille.keys())
    rows = []
    for eid in all_eids:
        emp = employes.get(eid)
        if not emp:
            continue
        reg = regions.get(emp.region_id)
        nb_actifs  = len(actifs.get(eid, set()))
        nb_total   = portefeuille.get(eid, 0)
        nb_inactifs = max(0, nb_total - nb_actifs)
        r_data = rec_agg.get(eid, {})
        rows.append({
            "employee_id":       eid,
            "nom":               f"{emp.prenom} {emp.nom}",
            "zone":              reg.nom if reg else "—",
            "type_poste":        emp.type_poste.value,
            # Recouvrement
            "ca_facture":        round(r_data.get("ca_facture", 0), 0),
            "ca_recouvre":       round(r_data.get("ca_recouvre", 0), 0),
            "taux_recouvrement": r_data.get("taux_recouvrement", 0),
            # Conversion / inactivité
            "nb_clients_actifs":   nb_actifs,
            "nb_clients_total":    nb_total,
            "nb_clients_inactifs": nb_inactifs,
            "taux_conversion":     round(nb_actifs / nb_total * 100, 1) if nb_total > 0 else 0.0,
            "pct_inactifs":        round(nb_inactifs / nb_total * 100, 1) if nb_total > 0 else 0.0,
        })

    return {
        "rows":          sorted(rows, key=lambda x: x["nom"]),
        "periode":       periode,
        "ranking_gamme": ranking_gamme,
    }
