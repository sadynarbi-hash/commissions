"""
Mise à jour des codes SAP (SlpCode) pour chaque commercial.
Lance avec : python -m app.seed_sap_codes
"""
from .database import SessionLocal
from .models.employee import Employee, Region

# (nom, prenom, region) → sap_code SAP
MAPPINGS = [
    # ── DAKAR ────────────────────────────────────────────
    ("DIAGNE",  "FATMA",           "DAKAR",  53),
    ("DIAGNE",  "MAMADOU",         "DAKAR",  52),
    ("MBAYE",   "EL H MANDOUMBE",  "DAKAR",  56),  # MANOUMBE MBAYE dans SAP
    ("FALL",    "IBRAHIMA",        "DAKAR",  54),
    ("KEBE",    "MOUSSA",          "DAKAR",  44),
    ("KONATE",  "ANTA",            "DAKAR",  26),
    ("DIOP",    "DIARRA",          "DAKAR",  25),  # MAME DIARRA DIOP dans SAP
    ("GOUDIABY","SOPHIE",          "DAKAR",  48),
    ("NIANG",   "MOUSSA",          "DAKAR",  50),  # SV Dakar
    ("FALL",    "AICHA",           "DAKAR",  61),  # HAICHA TALL dans SAP

    # ── NORD ─────────────────────────────────────────────
    ("NDIAYE",  "AMADOU KATY",     "NORD",   51),
    ("DIAGNE",  "MOUHAMED",        "NORD",   34),
    ("SOW",     "PAPE SAMBA",      "NORD",   29),  # PAPA SAMBA SOW dans SAP
    ("KA",      "SOGUI DIOUF",     "NORD",   49),
    ("AMAR",    "FATMA",           "NORD",   41),  # RCR
    ("MENDY",   "AMBROISE",        "NORD",   35),  # SV

    # ── CENTRE ───────────────────────────────────────────
    ("CISSOKHO","CHEIKH FILY",     "CENTRE",  6),  # CISSOKO FILY CHEIKH dans SAP
    ("NGOM",    "MODOU",           "CENTRE", 62),
    ("WADE",    "ALASSANE",        "CENTRE", 32),  # BAMBA WADE dans SAP
    ("GNINGUE", "PAPE MALICK",     "CENTRE", 31),
    ("WADE",    "KHADIME",         "CENTRE", 42),
    ("FAYE",    "PAPE FATA",       "CENTRE", 60),  # FATA FAYE dans SAP — RCR
    ("NDIAYE",  "ISMAILA",         "CENTRE", 59),  # SV

    # ── RESP. TECHNIQUE ──────────────────────────────────
    ("DIOP",    "NDEYE KHADY",     "CENTRE", 65),  # NDEYE KHADY DIAGNE dans SAP

    # ── DIRECTION ────────────────────────────────────────
    ("NDOYE",   "BABACAR",         "DAKAR",   4),  # DIR COMM dans SAP

    # ── SUD ──────────────────────────────────────────────
    ("YALLY",   "MEDOUNE",         "SUD",    55),
    ("KANTE",   "FATOUMATA",       "SUD",    15),
    ("TOURE",   "SERIGNE AMADOU",  "SUD",    36),
    ("BA",      "ISMA",            "SUD",    23),
    ("COLY",    "SOULEYMANE",      "SUD",     7),  # RCR
]


def run():
    db = SessionLocal()
    try:
        regions = {r.nom: r for r in db.query(Region).all()}
        updated = not_found = 0

        for nom, prenom, region_nom, sap_code in MAPPINGS:
            region = regions.get(region_nom)
            if not region:
                print(f"  ✗  Région '{region_nom}' introuvable")
                continue

            emp = db.query(Employee).filter(
                Employee.nom == nom,
                Employee.prenom == prenom,
                Employee.region_id == region.id,
            ).first()

            if emp:
                emp.sap_code = str(sap_code)
                print(f"  ✓  {prenom} {nom:<20} → SAP code {sap_code}")
                updated += 1
            else:
                print(f"  ✗  Introuvable : {prenom} {nom} / {region_nom}")
                not_found += 1

        db.commit()
        print(f"\n{'─'*50}")
        print(f"  {updated} code(s) SAP mis à jour | {not_found} introuvable(s)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
