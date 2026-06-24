"""Crée SAMORY TOURE — Responsable Technique Farine & Pâtes, SAP code 2."""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.employee import Employee, TypePoste, Region

db = SessionLocal()
try:
    existing = db.query(Employee).filter(
        Employee.nom == "TOURE",
        Employee.prenom == "SAMORY",
    ).first()

    if existing:
        existing.type_poste = TypePoste.RESP_TECH_FP
        existing.sap_code   = 2
        existing.actif      = True
        print(f"Mis à jour : ID={existing.id} SAMORY TOURE → RESP_TECH_FP, SAP=2")
    else:
        emp = Employee(
            prenom     = "SAMORY",
            nom        = "TOURE",
            type_poste = TypePoste.RESP_TECH_FP,
            sap_code   = 2,
            actif      = True,
            region_id  = None,
        )
        db.add(emp)
        db.flush()
        print(f"Créé : ID={emp.id} SAMORY TOURE → RESP_TECH_FP, SAP=2")

    db.commit()
    print("OK")
finally:
    db.close()
