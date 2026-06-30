from __future__ import annotations
from typing import Optional, List
from datetime import datetime, date
from calendar import monthrange
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..config import settings
from ..models.sales import SaleData, SyncLog, SyncSourceType, SyncStatut
from ..models.visit import VisitData, TypeVisite
from ..models.objective import Client, Gamme
from ..schemas.sync import SyncRequest, SyncLogRead, ConnectionTestRequest
from ..services.sap_connector import get_sap_connector
from ..services.sf_connector import get_sf_connector
from ..services.sync_sap import sync_sales, sync_geography

router = APIRouter(prefix="/api", tags=["sync"])


def _sync_sap_task(periode: str, db: Session):
    connector = get_sap_connector(settings)
    if not connector:
        raise ValueError("Connexion SAP non configurée")
    annee, mois = int(periode[:4]), int(periode[5:7])
    date_from = date(annee, mois, 1)
    date_to   = date(annee, mois, monthrange(annee, mois)[1])
    sync_sales(db, connector, date_from, date_to)


def _sync_sf_task(periode: str, db: Session):
    log = SyncLog(source=SyncSourceType.SALESFORCE, periode=periode, statut=SyncStatut.EN_COURS)
    db.add(log)
    db.commit()

    try:
        connector = get_sf_connector(settings)
        if not connector:
            raise ValueError("Connexion Salesforce non configurée")

        annee, mois = int(periode[:4]), int(periode[5:7])
        date_from = date(annee, mois, 1)
        date_to = date(annee, mois, monthrange(annee, mois)[1])

        from ..models.employee import Employee
        employees = db.query(Employee).filter(Employee.sf_id != None).all()
        sf_to_id = {e.sf_id: e.id for e in employees}

        # Supprimer les anciennes lignes SF pour cette période avant re-import
        db.query(VisitData).filter(
            VisitData.periode == periode,
            VisitData.visite_saisie_crm == True,
        ).delete(synchronize_session=False)
        db.flush()

        visits = connector.get_visits(date_from, date_to)
        nb = 0
        seen_sf_ids: set[str] = set()
        for v in visits:
            sf_id = v.get("Id")
            if not sf_id or sf_id in seen_sf_ids:
                continue
            seen_sf_ids.add(sf_id)

            # Champs venant de la tournée parente (Visite__c)
            visite_parent = v.get("Visite_id__r") or {}
            owner_id = visite_parent.get("OwnerId")
            datedone = visite_parent.get("Datedone__c")
            predicted = visite_parent.get("Predicted_date__c")

            # Date effective : VisiteLine > Datedone > Predicted
            line_date = v.get("date_de_visite__c")
            if line_date:
                visit_date = datetime.fromisoformat(line_date)
            elif datedone:
                visit_date = datetime.fromisoformat(datedone)
            elif predicted:
                visit_date = datetime.fromisoformat(predicted)
            else:
                visit_date = datetime.utcnow()

            compte = v.get("Account__r") or {}
            client_code = compte.get("SAP_Customer_Number__c") or v.get("Account__c")
            client_nom = compte.get("Name")

            division = (v.get("Division__c") or "").upper()
            if "FERME" in division or "ELEVAGE" in division:
                visit_type = TypeVisite.FERME
            elif "PROSPECT" in division:
                visit_type = TypeVisite.PROSPECTION
            else:
                visit_type = TypeVisite.CLIENT

            visit = VisitData(
                sf_id=sf_id,
                sf_owner_id=owner_id,
                employee_id=sf_to_id.get(owner_id),
                client_code=client_code,
                client_nom=client_nom,
                type_visite=visit_type,
                date_visite=visit_date,
                commande_saisie=False,
                visite_saisie_crm=True,
                kpis_json=None,
                periode=periode,
            )
            db.add(visit)
            nb += 1

        log.statut = SyncStatut.SUCCES
        log.nb_records = nb
        log.ended_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        log.statut = SyncStatut.ERREUR
        log.message = str(e)[:1000]
        log.ended_at = datetime.utcnow()
        db.commit()
        raise


def reattribute_visits(db: Session) -> dict:
    """Réattribue toutes les visites selon les sf_id actuels des employés.
    À appeler après toute correction de sf_id — pas besoin de re-syncer Salesforce.
    """
    from ..models.employee import Employee
    emps = db.query(Employee).filter(Employee.sf_id != None).all()
    sf_to_id = {e.sf_id: e.id for e in emps}

    updated = 0
    for sf_owner_id, emp_id in sf_to_id.items():
        result = db.execute(
            __import__('sqlalchemy').text(
                "UPDATE visits_data SET employee_id = :emp_id "
                "WHERE sf_owner_id = :sf_owner_id AND employee_id IS DISTINCT FROM :emp_id"
            ),
            {"emp_id": emp_id, "sf_owner_id": sf_owner_id},
        )
        updated += result.rowcount

    # Remettre à None les visites dont l'OwnerId n'est plus connu
    result = db.execute(
        __import__('sqlalchemy').text(
            "UPDATE visits_data SET employee_id = NULL "
            "WHERE sf_owner_id IS NOT NULL AND sf_owner_id NOT IN :known_ids AND employee_id IS NOT NULL"
        ),
        {"known_ids": tuple(sf_to_id.keys()) or ("",)},
    )
    db.commit()
    return {"updated": updated, "unlinked": result.rowcount}


@router.post("/sync")
def trigger_sync(body: SyncRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if body.source == SyncSourceType.SAP:
        background_tasks.add_task(_sync_sap_task, body.periode, db)
    else:
        background_tasks.add_task(_sync_sf_task, body.periode, db)
    return {"detail": f"Synchronisation {body.source.value} lancée pour {body.periode}"}


@router.get("/sync/logs", response_model=List[SyncLogRead])
def list_sync_logs(
    source: Optional[SyncSourceType] = None,
    db: Session = Depends(get_db),
):
    q = db.query(SyncLog)
    if source:
        q = q.filter(SyncLog.source == source)
    return q.order_by(SyncLog.started_at.desc()).limit(100).all()


@router.post("/sync/reattribute-visits")
def trigger_reattribute(db: Session = Depends(get_db)):
    """Réattribue toutes les visites selon les sf_id actuels — à appeler après fix sf_id."""
    result = reattribute_visits(db)
    return {"detail": f"{result['updated']} visite(s) réattribuée(s), {result['unlinked']} délié(s)"}


@router.post("/sync/geography")
def trigger_sync_geography(db: Session = Depends(get_db)):
    """Synchronise zones, secteurs et U_Secteur clients depuis SAP.
    À appeler une fois lors de la mise en place, puis après chaque mutation de secteur.
    """
    connector = get_sap_connector(settings)
    if not connector:
        raise HTTPException(status_code=503, detail="SAP non configuré")
    result = sync_geography(db, connector)
    return {"detail": "Sync géographie terminée", **result}


@router.post("/sync/test-connection")
def test_connection(body: ConnectionTestRequest):
    if body.source == SyncSourceType.SAP:
        connector = get_sap_connector(settings)
        if not connector:
            return {"ok": False, "message": "SAP non configuré"}
        ok = connector.test_connection()
        return {"ok": ok, "message": "Connexion réussie" if ok else "Échec de connexion"}
    else:
        connector = get_sf_connector(settings)
        if not connector:
            return {"ok": False, "message": "Salesforce non configuré"}
        ok = connector.test_connection()
        return {"ok": ok, "message": "Connexion réussie" if ok else "Échec de connexion"}
