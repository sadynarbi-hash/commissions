"""
Script de seed initial — Employés NMA 2026 (données réelles).
Lance avec : python -m app.seed
"""
from .database import SessionLocal
from .models.employee import Employee, Region, TypePoste, TypeRegion

# ─────────────────────────────────────────────────────────────────────────────
# DONNÉES COMPLÈTES
# type_poste : RCR | SV | COMMERCIAL | ATC_BV | RESP_TECH_BV | DV | DCMT
# ─────────────────────────────────────────────────────────────────────────────
EMPLOYEES = [

    # ── DIRECTION ────────────────────────────────────────────────────────────
    {"nom": "NDOYE",        "prenom": "BABACAR",        "type_poste": TypePoste.DCMT,         "region": "DAKAR",  "secteur": None},

    # ── RESPONSABLES RÉGIONAUX (RCR) ────────────────────────────────────────
    {"nom": "FALL",         "prenom": "AICHA",          "type_poste": TypePoste.RCR,          "region": "DAKAR",  "secteur": None},
    {"nom": "AMAR",         "prenom": "FATMA",          "type_poste": TypePoste.RCR,          "region": "NORD",   "secteur": None},
    {"nom": "FAYE",         "prenom": "PAPE FATA",      "type_poste": TypePoste.RCR,          "region": "CENTRE", "secteur": None},
    {"nom": "COLY",         "prenom": "SOULEYMANE",     "type_poste": TypePoste.RCR,          "region": "SUD",    "secteur": None},

    # ── SUPERVISEURS DES VENTES (SV) ────────────────────────────────────────
    {"nom": "NIANG",        "prenom": "MOUSSA",         "type_poste": TypePoste.SV,           "region": "DAKAR",  "secteur": None},
    {"nom": "NDIAYE",       "prenom": "ISMAILA",        "type_poste": TypePoste.SV,           "region": "CENTRE", "secteur": None},
    {"nom": "MENDY",        "prenom": "AMBROISE",       "type_poste": TypePoste.SV,           "region": "NORD",   "secteur": None},

    # ── RESPONSABLES TECHNIQUES BV (Docteurs) ───────────────────────────────
    {"nom": "DIOP",         "prenom": "NDEYE KHADY",    "type_poste": TypePoste.RESP_TECH_BV, "region": "CENTRE", "secteur": None},
    {"nom": "BA",           "prenom": "MARIAMA",        "type_poste": TypePoste.RESP_TECH_BV, "region": "DAKAR",  "secteur": None},

    # ── COMMERCIAUX DAKAR ───────────────────────────────────────────────────
    {"nom": "MBAYE",        "prenom": "EL H MANDOUMBE", "type_poste": TypePoste.COMMERCIAL,   "region": "DAKAR",  "secteur": "Banlieue 1"},
    {"nom": "DIAGNE",       "prenom": "MAMADOU",        "type_poste": TypePoste.COMMERCIAL,   "region": "DAKAR",  "secteur": "Plateau"},
    {"nom": "FALL",         "prenom": "IBRAHIMA",       "type_poste": TypePoste.COMMERCIAL,   "region": "DAKAR",  "secteur": "Banlieue 2"},
    {"nom": "KEBE",         "prenom": "MOUSSA",         "type_poste": TypePoste.COMMERCIAL,   "region": "DAKAR",  "secteur": "Banlieue 1"},
    {"nom": "DIAGNE",       "prenom": "FATMA",          "type_poste": TypePoste.COMMERCIAL,   "region": "DAKAR",  "secteur": "Plateau"},
    {"nom": "DIOP",         "prenom": "DIARRA",         "type_poste": TypePoste.COMMERCIAL,   "region": "DAKAR",  "secteur": "Banlieue 2"},
    {"nom": "KONATE",       "prenom": "ANTA",           "type_poste": TypePoste.COMMERCIAL,   "region": "DAKAR",  "secteur": "Plateau"},
    {"nom": "GOUDIABY",     "prenom": "SOPHIE",         "type_poste": TypePoste.ATC_BV,       "region": "DAKAR",  "secteur": "Grandes Fermes"},

    # ── COMMERCIAUX / ATC NORD ──────────────────────────────────────────────
    {"nom": "NDIAYE",       "prenom": "AMADOU KATY",    "type_poste": TypePoste.ATC_BV,       "region": "NORD",   "secteur": "Ourossogui"},
    {"nom": "SOW",          "prenom": "PAPE SAMBA",     "type_poste": TypePoste.COMMERCIAL,   "region": "NORD",   "secteur": "Saint-Louis"},
    {"nom": "KA",           "prenom": "SOGUI DIOUF",    "type_poste": TypePoste.COMMERCIAL,   "region": "NORD",   "secteur": "Ourossogui"},
    {"nom": "DIAGNE",       "prenom": "MOUHAMED",       "type_poste": TypePoste.ATC_BV,       "region": "NORD",   "secteur": "Saint-Louis"},

    # ── COMMERCIAUX / ATC CENTRE ────────────────────────────────────────────
    {"nom": "WADE",         "prenom": "KHADIME",        "type_poste": TypePoste.COMMERCIAL,   "region": "CENTRE", "secteur": "Mbour"},
    {"nom": "NGOM",         "prenom": "MODOU",          "type_poste": TypePoste.COMMERCIAL,   "region": "CENTRE", "secteur": "Touba"},
    {"nom": "CISSOKHO",     "prenom": "CHEIKH FILY",    "type_poste": TypePoste.COMMERCIAL,   "region": "CENTRE", "secteur": "Thiès"},
    {"nom": "WADE",         "prenom": "ALASSANE",       "type_poste": TypePoste.ATC_BV,       "region": "CENTRE", "secteur": "Thiès"},
    {"nom": "GNINGUE",      "prenom": "PAPE MALICK",    "type_poste": TypePoste.ATC_BV,       "region": "CENTRE", "secteur": "Touba"},

    # ── COMMERCIAUX / ATC SUD ───────────────────────────────────────────────
    {"nom": "YALLY",        "prenom": "MEDOUNE",        "type_poste": TypePoste.COMMERCIAL,   "region": "SUD",    "secteur": "Kaolack"},
    {"nom": "KANTE",        "prenom": "FATOUMATA",      "type_poste": TypePoste.COMMERCIAL,   "region": "SUD",    "secteur": "Ziguinchor"},
    {"nom": "TOURE",        "prenom": "SERIGNE AMADOU", "type_poste": TypePoste.ATC_BV,       "region": "SUD",    "secteur": "Kaolack"},
    {"nom": "BA",           "prenom": "ISMA",           "type_poste": TypePoste.ATC_BV,       "region": "SUD",    "secteur": "Ziguinchor"},
]


def _ensure_regions(db):
    REGIONS = [
        ("DAKAR",  TypeRegion.NATIONALE),
        ("NORD",   TypeRegion.NATIONALE),
        ("CENTRE", TypeRegion.NATIONALE),
        ("SUD",    TypeRegion.NATIONALE),
        ("EXPORT", TypeRegion.EXPORT),
    ]
    for nom, type_region in REGIONS:
        if not db.query(Region).filter(Region.nom == nom).first():
            db.add(Region(nom=nom, type=type_region))
            print(f"  +  Région {nom}")
    db.commit()


def run():
    db = SessionLocal()
    try:
        _ensure_regions(db)
        regions = {r.nom: r for r in db.query(Region).all()}
        created = 0

        for data in EMPLOYEES:
            region = regions.get(data["region"])
            if not region:
                print(f"  ⚠  Région '{data['region']}' introuvable — ignoré")
                continue

            exists = db.query(Employee).filter(
                Employee.nom == data["nom"],
                Employee.prenom == data["prenom"],
                Employee.region_id == region.id,
            ).first()

            nom_complet = f"{data['prenom']} {data['nom']}"
            if exists:
                print(f"  =  {nom_complet}")
            else:
                db.add(Employee(
                    nom=data["nom"],
                    prenom=data["prenom"],
                    type_poste=data["type_poste"],
                    region_id=region.id,
                    secteur=data.get("secteur"),
                    actif=True,
                ))
                created += 1
                print(f"  +  {nom_complet:<30} {data['type_poste'].value:<14} {data['region']}")

        db.commit()
        print(f"\n{'─'*60}")
        print(f"  {created} employé(s) créé(s).")
    finally:
        db.close()


if __name__ == "__main__":
    run()
