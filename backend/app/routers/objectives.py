from __future__ import annotations
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.objective import Objective, SalesForecast, Client, ClientPortfolio, Gamme
from ..schemas.objective import (
    ObjectiveCreate, ObjectiveRead, ObjectiveUpdate,
    SalesForecastCreate, SalesForecastRead,
    ClientCreate, ClientRead, PortfolioAssign,
)

router = APIRouter(prefix="/api", tags=["objectives"])


@router.get("/objectives", response_model=List[ObjectiveRead])
def list_objectives(
    periode: Optional[str] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Objective)
    if periode:
        q = q.filter(Objective.periode == periode)
    if employee_id:
        q = q.filter(Objective.employee_id == employee_id)
    return q.all()


@router.post("/objectives", response_model=ObjectiveRead, status_code=201)
def upsert_objective(body: ObjectiveCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(Objective)
        .filter(
            Objective.employee_id == body.employee_id,
            Objective.periode == body.periode,
            Objective.gamme == body.gamme,
        )
        .first()
    )
    if existing:
        existing.objectif_volume = body.objectif_volume
        existing.objectif_ca = body.objectif_ca
        db.commit()
        db.refresh(existing)
        return existing
    obj = Objective(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/objectives/{objective_id}", status_code=204)
def delete_objective(objective_id: int, db: Session = Depends(get_db)):
    obj = db.query(Objective).filter(Objective.id == objective_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif introuvable")
    db.delete(obj)
    db.commit()


@router.get("/forecasts", response_model=List[SalesForecastRead])
def list_forecasts(
    periode: Optional[str] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(SalesForecast)
    if periode:
        q = q.filter(SalesForecast.periode == periode)
    if employee_id:
        q = q.filter(SalesForecast.employee_id == employee_id)
    return q.all()


@router.post("/forecasts", response_model=SalesForecastRead, status_code=201)
def upsert_forecast(body: SalesForecastCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(SalesForecast)
        .filter(
            SalesForecast.employee_id == body.employee_id,
            SalesForecast.periode == body.periode,
            SalesForecast.gamme == body.gamme,
        )
        .first()
    )
    if existing:
        existing.volume_prevu = body.volume_prevu
        existing.ca_prevu = body.ca_prevu
        db.commit()
        db.refresh(existing)
        return existing
    f = SalesForecast(**body.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@router.get("/clients", response_model=List[ClientRead])
def list_clients(db: Session = Depends(get_db)):
    return db.query(Client).order_by(Client.nom).all()


@router.post("/clients", response_model=ClientRead, status_code=201)
def create_client(body: ClientCreate, db: Session = Depends(get_db)):
    client = Client(**body.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.post("/portfolio", status_code=201)
def assign_portfolio(body: PortfolioAssign, db: Session = Depends(get_db)):
    existing = (
        db.query(ClientPortfolio)
        .filter(
            ClientPortfolio.employee_id == body.employee_id,
            ClientPortfolio.client_id == body.client_id,
            ClientPortfolio.annee == body.annee,
        )
        .first()
    )
    if existing:
        return {"detail": "déjà affecté"}
    p = ClientPortfolio(**body.model_dump())
    db.add(p)
    db.commit()
    return {"detail": "affecté"}


@router.get("/portfolio/{employee_id}/{annee}", response_model=List[ClientRead])
def get_portfolio(employee_id: int, annee: int, db: Session = Depends(get_db)):
    rows = (
        db.query(Client)
        .join(ClientPortfolio)
        .filter(
            ClientPortfolio.employee_id == employee_id,
            ClientPortfolio.annee == annee,
        )
        .all()
    )
    return rows
