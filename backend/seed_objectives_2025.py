"""
Seed objectifs Sep-Déc 2025 (données SAP extraites depuis Excel).
Gamme = ALL (total par commercial, pas de ventilation par gamme disponible).
"""
from app.database import SessionLocal
from app.models.objective import Objective, Gamme
from app.models.employee import Employee
from sqlalchemy.dialects.postgresql import insert

db = SessionLocal()

# (periode, nom_sap, objectif_volume_tonnes)
# Noms SAP → cherchés par nom dans notre base
OBJECTIFS = [
    # ── Septembre 2025 ──────────────────────────────────────────────
    ("2025-09", "ALASSANE WADE",         3075),
    ("2025-09", "AMADOU KATY NDIAYE",     600),
    ("2025-09", "ANTA KONATE",            135),
    ("2025-09", "CHEIKH FILY CISSOKHO",   763),
    ("2025-09", "DIARRA DIOP",             95),
    ("2025-09", "EL H MANDOUMBE MBAYE",  3410),
    ("2025-09", "FATMA DIAGNE",           970),
    ("2025-09", "FATOUMATA KANTE",         30),
    ("2025-09", "IBRAHIMA FALL",          2350),
    ("2025-09", "ISMA BA",                1250),
    ("2025-09", "KHADIME WADE",           2370),
    ("2025-09", "MAMADOU DIAGNE",         2485),
    ("2025-09", "MEDOUNE YALLY",          1220),
    ("2025-09", "MODOU NGOM",             1937),
    ("2025-09", "MOUHAMED DIAGNE",        2400),
    ("2025-09", "MOUSSA KEBE",            1215),
    ("2025-09", "PAPE MALICK GNINGUE",    1305),
    ("2025-09", "PAPE SAMBA SOW",          375),
    ("2025-09", "SOGUI DIOUF KA",          225),
    ("2025-09", "SOPHIE GOUDIABY",         400),
    ("2025-09", "SERIGNE AMADOU TOURE",   None),  # TOURE SAMORY/AMADOU TOURE — sans tonnage visible

    # ── Octobre 2025 ────────────────────────────────────────────────
    ("2025-10", "ALASSANE WADE",         3849),
    ("2025-10", "AMADOU KATY NDIAYE",     700),
    ("2025-10", "ANTA KONATE",            200),
    ("2025-10", "CHEIKH FILY CISSOKHO",   758),
    ("2025-10", "DIARRA DIOP",            140),
    ("2025-10", "EL H MANDOUMBE MBAYE",  4400),
    ("2025-10", "FATMA DIAGNE",          1000),
    ("2025-10", "FATOUMATA KANTE",         40),
    ("2025-10", "IBRAHIMA FALL",          3100),
    ("2025-10", "ISMA BA",                1625),
    ("2025-10", "KHADIME WADE",           2968),
    ("2025-10", "MAMADOU DIAGNE",         2700),
    ("2025-10", "MEDOUNE YALLY",          1810),
    ("2025-10", "MODOU NGOM",             1892),
    ("2025-10", "MOUHAMED DIAGNE",        3000),
    ("2025-10", "MOUSSA KEBE",            1375),
    ("2025-10", "PAPE MALICK GNINGUE",    1633),
    ("2025-10", "PAPE SAMBA SOW",          400),
    ("2025-10", "SOGUI DIOUF KA",          300),
    ("2025-10", "SOPHIE GOUDIABY",         400),

    # ── Novembre 2025 ───────────────────────────────────────────────
    ("2025-11", "ALASSANE WADE",         4079),
    ("2025-11", "AMADOU KATY NDIAYE",     700),
    ("2025-11", "ANTA KONATE",            180),
    ("2025-11", "CHEIKH FILY CISSOKHO",   785),
    ("2025-11", "DIARRA DIOP",            130),
    ("2025-11", "EL H MANDOUMBE MBAYE",  4300),
    ("2025-11", "FATMA DIAGNE",          1050),
    ("2025-11", "FATOUMATA KANTE",         55),
    ("2025-11", "IBRAHIMA FALL",          3200),
    ("2025-11", "ISMA BA",                1625),
    ("2025-11", "KHADIME WADE",           3138),
    ("2025-11", "MAMADOU DIAGNE",         2700),
    ("2025-11", "MEDOUNE YALLY",          1845),
    ("2025-11", "MODOU NGOM",             1965),
    ("2025-11", "MOUHAMED DIAGNE",        3000),
    ("2025-11", "MOUSSA KEBE",            1405),
    ("2025-11", "PAPE MALICK GNINGUE",    1733),
    ("2025-11", "PAPE SAMBA SOW",          550),
    ("2025-11", "SOGUI DIOUF KA",          400),
    ("2025-11", "SOPHIE GOUDIABY",         400),

    # ── Décembre 2025 ───────────────────────────────────────────────
    ("2025-12", "ALASSANE WADE",         4079),
    ("2025-12", "AMADOU KATY NDIAYE",     900),
    ("2025-12", "ANTA KONATE",            150),
    ("2025-12", "CHEIKH FILY CISSOKHO",   763),
    ("2025-12", "DIARRA DIOP",            105),
    ("2025-12", "EL H MANDOUMBE MBAYE",  4500),
    ("2025-12", "FATMA DIAGNE",          1050),
    ("2025-12", "FATOUMATA KANTE",         30),
    ("2025-12", "IBRAHIMA FALL",          3350),
    ("2025-12", "ISMA BA",                1625),
    ("2025-12", "KHADIME WADE",           3138),
    ("2025-12", "MAMADOU DIAGNE",         2700),
    ("2025-12", "MEDOUNE YALLY",          1770),
    ("2025-12", "MODOU NGOM",             1937),
    ("2025-12", "MOUHAMED DIAGNE",        3100),
    ("2025-12", "MOUSSA KEBE",            1360),
    ("2025-12", "PAPE MALICK GNINGUE",    1733),
    ("2025-12", "PAPE SAMBA SOW",          575),
    ("2025-12", "SOGUI DIOUF KA",          425),
    ("2025-12", "SOPHIE GOUDIABY",         400),
]

# Cache employés
employees = db.query(Employee).all()

def find_employee(name: str):
    parts = name.upper().split()
    for emp in employees:
        full = f"{emp.prenom} {emp.nom}".upper()
        if full == name.upper():
            return emp
    # Recherche par nom (dernier mot)
    nom = parts[-1]
    prenom = " ".join(parts[:-1])
    for emp in employees:
        if emp.nom.upper() == nom and emp.prenom.upper() == prenom:
            return emp
    # Recherche partielle sur nom seul
    for emp in employees:
        if emp.nom.upper() == nom:
            candidates = [e for e in employees if e.nom.upper() == nom]
            if len(candidates) == 1:
                return candidates[0]
    return None

ok, skip = 0, []
for periode, nom_sap, volume in OBJECTIFS:
    emp = find_employee(nom_sap)
    if not emp:
        skip.append(f"{periode} {nom_sap}")
        continue

    # Upsert
    existing = db.query(Objective).filter(
        Objective.employee_id == emp.id,
        Objective.periode == periode,
        Objective.gamme == Gamme.ALL,
    ).first()
    if existing:
        existing.objectif_volume = volume
    else:
        db.add(Objective(
            employee_id=emp.id,
            periode=periode,
            gamme=Gamme.ALL,
            objectif_volume=volume,
        ))
    ok += 1

db.commit()
print(f"Importé : {ok} objectifs")
if skip:
    print(f"Non trouvés ({len(skip)}) :")
    for s in skip:
        print(f"  - {s}")
db.close()
