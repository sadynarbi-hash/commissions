"""Corrige les sf_id Salesforce incorrects et réattribue tout l'historique des visites."""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.employee import Employee
from app.routers.sync import reattribute_visits

CORRECTIONS = [
    # (prenom, nom, sf_id_correct)
    ("ANTA",           "KONATE",  "0054L0000033OnKQAU"),  # avait un zéro en trop
    ("FATMA",          "DIAGNE",  "0054L0000033XprQAE"),  # Xv -> Xpr
    ("SERIGNE AMADOU", "TOURE",   "0054L000003sD27QAE"),  # El Hadji Amadou Touré dans SF
]

db = SessionLocal()
try:
    for prenom, nom, sf_id in CORRECTIONS:
        emp = db.query(Employee).filter(
            Employee.prenom == prenom,
            Employee.nom == nom,
        ).first()
        if emp:
            old = emp.sf_id
            emp.sf_id = sf_id
            print(f"{prenom} {nom}: {old} -> {sf_id}")
        else:
            print(f"INTROUVABLE: {prenom} {nom}")
    db.commit()

    print("Réattribution des visites...")
    result = reattribute_visits(db)
    print(f"  {result['updated']} visite(s) réattribuée(s)")
    print("OK")
finally:
    db.close()
