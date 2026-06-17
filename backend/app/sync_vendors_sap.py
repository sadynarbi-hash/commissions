"""
Synchronise la table OSLP (vendeurs SAP) vers employees.
- Met à jour le sap_code des employés existants si le nom correspond.
- Crée les vendeurs inconnus avec actif=False (hors calcul primes).
"""
import sys
from app.database import SessionLocal
from app.config import settings
from app.services.sap_connector import get_sap_connector
from app.models.employee import Employee, TypePoste

# Vendeurs génériques SAP à ignorer
IGNORES = {
    "EXPORT", "AUTRE", "DIR COMM", "COMMERCIAL KAOLACK",
    "KONATE ALIOUNE", "TOURE SAMORY", "MBODJI BASSIROU",
    "MALE ABDOULAYE", "EL HADJI GUEYE", "NDIONE SOULEYMANE",
    "SALL IBRAHIMA", "SENE FALILOU", "SY CHEIKH AHMETH TIDIANE",
    "ABDOULAYE DIOP", "ABDOULAYE HANE", "MOUSSA NDIAYE",
    "MADIAGNE NIANE", "FARA NDOYE", "LAMINE SARR", "CHEIKH DIOP",
    "CONSTANCE BASSENE", "DR FALL", "EMMANUEL ELIE", "OUMAR LY",
    "SADANI KOTE", "SOUMARE", "MALICK NIANG", "YACINE NIANG",
    "FARIMA SADY", "FATOU TALL",
}

def sync_vendors():
    db = SessionLocal()
    connector = get_sap_connector(settings)

    vendors = connector.execute_query("SELECT SlpCode, SlpName FROM OSLP WHERE Locked = ?", ("N",))

    existing_codes = {e.sap_code: e for e in db.query(Employee).all() if e.sap_code}

    created = 0
    skipped = 0
    already = 0

    for v in vendors:
        code = str(v["SlpCode"])
        name = (v["SlpName"] or "").strip().upper()

        if name in IGNORES:
            skipped += 1
            continue

        if code in existing_codes:
            already += 1
            continue

        # Nouveau vendeur : split nom/prénom sur le premier espace
        parts = name.split(" ", 1)
        prenom = parts[0] if len(parts) > 1 else ""
        nom    = parts[1] if len(parts) > 1 else parts[0]

        emp = Employee(
            nom=nom,
            prenom=prenom,
            sap_code=code,
            type_poste=TypePoste.COMMERCIAL,
            actif=False,
        )
        db.add(emp)
        created += 1
        print(f"  + {code:>3}  {name}")

    db.commit()
    db.close()

    print(f"\nRésultat : {created} ajoutés, {already} déjà en base, {skipped} ignorés")

if __name__ == "__main__":
    sync_vendors()
