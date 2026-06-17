"""
Seed zones, secteurs géographiques et secteurs commerciaux
depuis les données extraites des tables SAP (@ZONESLIGNES, @SECTEURSLIGNE, @COMSECTEURLIGNE).
Utilisable hors connexion SAP.
"""
from __future__ import annotations
from app.database import SessionLocal, engine, Base
from app.models.geography import Zone, SecteurGeo, Secteur
from app.models.employee import Employee

# ── Données @ZONESLIGNES ──────────────────────────────────────────────────────
ZONES = [
    # (code, nom, superviseur, responsable, docteur)
    ("Z1", "DAKAR",   "MOUSSA NIANG",    "AICHA FALL",      "MARIAMA BA"),
    ("Z2", "CENTRE",  "ISMAILA NDIAYE",  "PAPE FATA FAYE",  "NDEYE KHADY DIOP"),
    ("Z3", "NORD",    "AMBROISE MENDY",  "FATMA AMAR",      "NDEYE KHADY DIOP"),
    ("Z4", "SUD",     "SOULEYMANE COLY", "SOULEYMANE COLY", "MARIAMA BA"),
    ("Z5", "EXPORT",  None,              None,              None),
    ("Z6", "NMA",     None,              None,              None),
]

# ── Données @SECTEURSLIGNE ────────────────────────────────────────────────────
SECTEURS_GEO = [
    # (code, nom, zone_code)
    ("Z1S1",  "Plateau",         "Z1"),
    ("Z1S2",  "Banlieue 1",      "Z1"),
    ("Z1S3",  "Banlieue 2",      "Z1"),
    ("Z1S4",  "Grandes Fermes",  "Z1"),
    ("Z2S1",  "Thies",           "Z2"),
    ("Z2S2",  "Touba",           "Z2"),
    ("Z2S3",  "Mbour",           "Z2"),
    ("Z3S1",  "Saint-Louis",     "Z3"),
    ("Z3S2",  "Ourossogui",      "Z3"),
    ("Z4S1",  "Kaolack",         "Z4"),
    ("Z4S2",  "Ziguinchor",      "Z4"),
    ("Z4S3",  "Tambacounda",     "Z4"),
    ("Z1DCM", "Dakar DCM",       "Z1"),
    ("Z2DCM", "Centre DCM",      "Z2"),
    ("Z3DCM", "Nord DCM",        "Z3"),
    ("Z4DCM", "Sud DCM",         "Z4"),
    ("EXPORT","Export",          "Z5"),
]

# ── Données @COMSECTEURLIGNE ──────────────────────────────────────────────────
# (code_U_CODE, secteur_geo, gamme, commercial)
SECTEURS_COM = [
    ("Z1S1BV",  "Z1S1",  "BETAIL/VOL",  "MAMADOU DIAGNE"),
    ("Z1S1FA",  "Z1S1",  "FARINE",      "FATMA DIAGNE"),
    ("Z1S1PA",  "Z1S1",  "PATE",        "ANTA KONATE"),
    ("Z1S2BV",  "Z1S2",  "BETAIL/VOL",  "EL H MANDOUMBE MBAYE"),
    ("Z1S2PA",  "Z1S2",  "PATE",        "MOUSSA KEBE"),
    ("Z1S3BV",  "Z1S3",  "BETAIL/VOL",  "IBRAHIMA FALL"),
    ("Z1S3PA",  "Z1S3",  "PATE",        "DIARRA DIOP"),
    ("Z1S4BV",  "Z1S4",  "BETAIL/VOL",  "SOPHIE GOUDIABY"),
    ("Z2S1BV",  "Z2S1",  "BETAIL/VOL",  "ALASSANE WADE"),
    ("Z2S1FA",  "Z2S1",  "FARINE",      "CHEIKH FILY CISSOKHO"),
    ("Z2S1PA",  "Z2S1",  "PATE",        "CHEIKH FILY CISSOKHO"),
    ("Z2S2BV",  "Z2S2",  "BETAIL/VOL",  "PAPE MALICK GNINGUE"),
    ("Z2S2FA",  "Z2S2",  "FARINE",      "MODOU NGOM"),
    ("Z2S2PA",  "Z2S2",  "PATE",        "MODOU NGOM"),
    ("Z2S3BV",  "Z2S3",  "BETAIL/VOL",  "KHADIME WADE"),
    ("Z2S3FA",  "Z2S3",  "FARINE",      "CHEIKH FILY CISSOKHO"),
    ("Z2S3PA",  "Z2S3",  "PATE",        "CHEIKH FILY CISSOKHO"),
    ("Z3S1BV",  "Z3S1",  "BETAIL/VOL",  "MOUHAMED DIAGNE"),
    ("Z3S1PF",  "Z3S1",  "PATE/FARINE", "PAPE SAMBA SOW"),
    ("Z3S2BV",  "Z3S2",  "BETAIL/VOL",  "AMADOU KATY NDIAYE"),
    ("Z3S2PF",  "Z3S2",  "PATE/FARINE", "SOGUI DIOUF KA"),
    ("Z4S1BV",  "Z4S1",  "BETAIL/VOL",  "SERIGNE AMADOU TOURE"),
    ("Z4S1FA",  "Z4S1",  "FARINE",      "MEDOUNE YALLY"),
    ("Z4S1PA",  "Z4S1",  "PATE",        "MEDOUNE YALLY"),
    ("Z4S2BV",  "Z4S2",  "BETAIL/VOL",  "ISMA BA"),
    ("Z4S2PA",  "Z4S2",  "PATE",        "FATOUMATA KANTE"),
    ("Z4S3BV",  "Z4S3",  "BETAIL/VOL",  "MEDOUNE YALLY"),
    ("Z4S3PA",  "Z4S3",  "PATE",        "MEDOUNE YALLY"),
    ("Z1DCM",   "Z1DCM", "ALL",         "BABACAR NDOYE"),
    ("Z2DCM",   "Z2DCM", "ALL",         "BABACAR NDOYE"),
    ("Z3DCM",   "Z3DCM", "ALL",         "BABACAR NDOYE"),
    ("Z4DCM",   "Z4DCM", "ALL",         "BABACAR NDOYE"),
]


def _find_employee(db, nom: str | None):
    if not nom:
        return None
    nom_up = nom.strip().upper()
    emps = db.query(Employee).filter(Employee.actif == True).all()
    # 1. Exact
    for e in emps:
        if f"{e.prenom} {e.nom}".upper() == nom_up:
            return e.id
    # 2. Nom SAP tronqué dans nom complet — ex: "FATMA DIA" in "FATMA DIAGNE"
    for e in emps:
        if nom_up in f"{e.prenom} {e.nom}".upper():
            return e.id
    # 3. Nom complet dans nom SAP
    for e in emps:
        if f"{e.prenom} {e.nom}".upper() in nom_up:
            return e.id
    return None


def seed(db=None):
    close = db is None
    if db is None:
        Base.metadata.create_all(engine)
        db = SessionLocal()

    try:
        # ── Zones ─────────────────────────────────────────────────────────
        for code, nom, sup_nom, resp_nom, doc_nom in ZONES:
            zone = db.query(Zone).filter(Zone.code == code).first()
            if not zone:
                zone = Zone(code=code, nom=nom)
                db.add(zone)
            else:
                zone.nom = nom
            zone.superviseur_id = _find_employee(db, sup_nom)
            zone.responsable_id = _find_employee(db, resp_nom)
            zone.docteur_id     = _find_employee(db, doc_nom)
        db.flush()
        print(f"  {len(ZONES)} zones seedées")

        zones_by_code = {z.code: z for z in db.query(Zone).all()}

        # ── Secteurs géographiques ─────────────────────────────────────────
        for code, nom, zone_code in SECTEURS_GEO:
            zone = zones_by_code.get(zone_code)
            sg = db.query(SecteurGeo).filter(SecteurGeo.code == code).first()
            if not sg:
                sg = SecteurGeo(code=code, nom=nom, zone_id=zone.id if zone else None)
                db.add(sg)
            else:
                sg.nom     = nom
                sg.zone_id = zone.id if zone else sg.zone_id
        db.flush()
        print(f"  {len(SECTEURS_GEO)} secteurs géographiques seedés")

        # ── Secteurs commerciaux ───────────────────────────────────────────
        for code, geo_code, gamme, commercial_nom in SECTEURS_COM:
            sec = db.query(Secteur).filter(Secteur.code == code).first()
            if not sec:
                sec = Secteur(code=code, gamme=gamme, secteur_geo_code=geo_code)
                db.add(sec)
            else:
                sec.gamme            = gamme
                sec.secteur_geo_code = geo_code
            sec.employee_id = _find_employee(db, commercial_nom)
        db.flush()
        print(f"  {len(SECTEURS_COM)} secteurs commerciaux seedés")

        db.commit()
        print("Seed zones terminé.")

    finally:
        if close:
            db.close()


if __name__ == "__main__":
    seed()
