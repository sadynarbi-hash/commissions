from __future__ import annotations
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.employee import Employee, Region
from ..schemas.employee import (
    EmployeeCreate, EmployeeRead, EmployeeUpdate,
    RegionCreate, RegionRead,
)

router = APIRouter(prefix="/api", tags=["employees"])


@router.get("/regions", response_model=List[RegionRead])
def list_regions(db: Session = Depends(get_db)):
    return db.query(Region).order_by(Region.nom).all()


@router.post("/regions", response_model=RegionRead, status_code=201)
def create_region(body: RegionCreate, db: Session = Depends(get_db)):
    region = Region(**body.model_dump())
    db.add(region)
    db.commit()
    db.refresh(region)
    return region


@router.get("/employees", response_model=List[EmployeeRead])
def list_employees(
    actif: Optional[bool] = None,
    region_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Employee)
    if actif is not None:
        q = q.filter(Employee.actif == actif)
    if region_id is not None:
        q = q.filter(Employee.region_id == region_id)
    return q.order_by(Employee.nom, Employee.prenom).all()


@router.get("/employees/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employé introuvable")
    return emp


@router.post("/employees", response_model=EmployeeRead, status_code=201)
def create_employee(body: EmployeeCreate, db: Session = Depends(get_db)):
    emp = Employee(**body.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.patch("/employees/{employee_id}", response_model=EmployeeRead)
def update_employee(employee_id: int, body: EmployeeUpdate, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employé introuvable")
    for key, value in body.model_dump(exclude_none=True).items():
        setattr(emp, key, value)
    db.commit()
    db.refresh(emp)
    return emp


@router.delete("/employees/{employee_id}", status_code=204)
def deactivate_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employé introuvable")
    emp.actif = False
    db.commit()
