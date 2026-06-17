"""
Seed des objectifs 2026 — données réelles par commercial et par gamme.
Sources : centre.pdf, nord.pdf, Sud.pdf, Dakar.pdf
Lance avec : python -m app.seed_objectives
"""
from .database import SessionLocal
from .models.employee import Employee, Region
from .models.objective import Objective, Gamme

# ─── helpers ──────────────────────────────────────────────────────────────────
def _mois(nums: list, start_month: int = 1) -> dict:
    """Associe une liste de volumes aux périodes 2026-MM."""
    return {f"2026-{start_month + i:02d}": v for i, v in enumerate(nums)}


# ─── DONNÉES OBJECTIFS ────────────────────────────────────────────────────────
# Format : (nom, prenom, region, gamme, dict{periode: volume})
# CENTRE : mars→décembre (10 mois)   NORD/DAKAR : jan→déc (12 mois)
# SUD    : mars→décembre (10 mois)

OBJECTIVES = [

    # ══ ZONE CENTRE ══════════════════════════════════════════════════════════
    # CHEIKH FILY CISSOKHO — FARINE (Thiès + Fatick)
    ("CISSOKHO", "CHEIKH FILY", "CENTRE", Gamme.FARINE,
     _mois([624, 600, 600, 600, 600, 600, 576, 600, 624, 624], 3)),

    # CHEIKH FILY CISSOKHO — PATES (Thiès + Fatick)
    ("CISSOKHO", "CHEIKH FILY", "CENTRE", Gamme.PATES,
     _mois([201.6, 108, 100.8, 122.4, 122.4, 129.6, 108, 108, 133.2, 126], 3)),

    # MODOU NGOM — FARINE (Touba)
    ("NGOM", "MODOU", "CENTRE", Gamme.FARINE,
     _mois([1976, 1900, 1900, 1900, 1900, 1900, 1824, 1900, 1976, 1976], 3)),

    # MODOU NGOM — PATES (Touba)
    ("NGOM", "MODOU", "CENTRE", Gamme.PATES,
     _mois([78.4, 42, 39.2, 47.6, 47.6, 50.4, 42, 42, 51.8, 49], 3)),

    # ALASSANE WADE — VOLAILLE (Thiès + Fatick + Mbour)
    ("WADE", "ALASSANE", "CENTRE", Gamme.VOLAILLE,
     _mois([5846, 5032, 4440, 5365, 6068, 4810, 5846, 5920, 5920, 6105], 3)),

    # ALASSANE WADE — BETAIL (Thiès + Fatick + Mbour)
    ("WADE", "ALASSANE", "CENTRE", Gamme.BETAIL,
     _mois([682, 1116, 1054, 1054, 930, 682, 620, 620, 682, 682], 3)),

    # PAPE MALICK GNINGUE — VOLAILLE (Touba)
    ("GNINGUE", "PAPE MALICK", "CENTRE", Gamme.VOLAILLE,
     _mois([2054, 1768, 1560, 1885, 2132, 1690, 2054, 2080, 2080, 2145], 3)),

    # PAPE MALICK GNINGUE — BETAIL (Touba)
    ("GNINGUE", "PAPE MALICK", "CENTRE", Gamme.BETAIL,
     _mois([418, 684, 646, 646, 570, 418, 380, 380, 418, 418], 3)),

    # ══ ZONE NORD ═══════════════════════════════════════════════════════════
    # AMADOU KATY NDIAYE — VOLAILLE (Axe Podor-Bakel)
    ("NDIAYE", "AMADOU KATY", "NORD", Gamme.VOLAILLE,
     _mois([700, 600, 500, 400, 300, 300, 300, 400, 400, 500, 500, 700], 1)),

    # AMADOU KATY NDIAYE — BETAIL (Axe Podor-Bakel)
    ("NDIAYE", "AMADOU KATY", "NORD", Gamme.BETAIL,
     _mois([200, 300, 200, 500, 500, 200, 500, 300, 200, 200, 200, 200], 1)),

    # MOUHAMED DIAGNE — VOLAILLE (Axe Louga-Saint-Louis)
    ("DIAGNE", "MOUHAMED", "NORD", Gamme.VOLAILLE,
     _mois([1800, 2000, 2200, 1800, 1700, 1900, 2300, 1600, 2100, 2000, 2100, 2000], 1)),

    # MOUHAMED DIAGNE — BETAIL (Axe Louga-Saint-Louis)
    ("DIAGNE", "MOUHAMED", "NORD", Gamme.BETAIL,
     _mois([1800, 1700, 2000, 3000, 3000, 3000, 2000, 1800, 1600, 1600, 1800, 1900], 1)),

    # SOGUI DIOUF KA — FARINE (Axe Podor-Bakel)
    ("KA", "SOGUI DIOUF", "NORD", Gamme.FARINE,
     _mois([50, 100, 100, 100, 100, 80, 100, 100, 80, 100, 90, 100], 1)),

    # SOGUI DIOUF KA — PATES (Axe Podor-Bakel)
    ("KA", "SOGUI DIOUF", "NORD", Gamme.PATES,
     _mois([275, 200, 275, 200, 275, 200, 200, 200, 200, 200, 250, 275], 1)),

    # PAPE SAMBA SOW — FARINE (Axe Louga-Saint-Louis)
    ("SOW", "PAPE SAMBA", "NORD", Gamme.FARINE,
     _mois([400, 400, 400, 400, 400, 400, 400, 400, 400, 400, 450, 450], 1)),

    # PAPE SAMBA SOW — PATES (Axe Louga-Saint-Louis)
    ("SOW", "PAPE SAMBA", "NORD", Gamme.PATES,
     _mois([125, 100, 125, 100, 125, 100, 100, 100, 100, 100, 100, 125], 1)),

    # ══ ZONE SUD ════════════════════════════════════════════════════════════
    # FATOUMATA KANTE — PATES (Ziguinchor)
    ("KANTE", "FATOUMATA", "SUD", Gamme.PATES,
     _mois([50, 30, 40, 30, 40, 30, 30, 30, 40, 40], 3)),

    # MEDOUNE YALLY — PATES
    ("YALLY", "MEDOUNE", "SUD", Gamme.PATES,
     _mois([325, 185, 310, 230, 260, 220, 220, 220, 285, 285], 3)),

    # MEDOUNE YALLY — FARINE
    ("YALLY", "MEDOUNE", "SUD", Gamme.FARINE,
     _mois([650, 600, 600, 600, 600, 550, 550, 550, 600, 600], 3)),

    # MEDOUNE YALLY — BETAIL
    ("YALLY", "MEDOUNE", "SUD", Gamme.BETAIL,
     _mois([170, 270, 280, 200, 200, 100, 100, 110, 120, 120], 3)),

    # MEDOUNE YALLY — VOLAILLE
    ("YALLY", "MEDOUNE", "SUD", Gamme.VOLAILLE,
     _mois([690, 610, 440, 610, 610, 470, 640, 670, 720, 915], 3)),

    # SERIGNE AMADOU TOURE — BETAIL (Kaolack-Kaffrine)
    ("TOURE", "SERIGNE AMADOU", "SUD", Gamme.BETAIL,
     _mois([265, 365, 385, 300, 300, 200, 200, 220, 240, 240], 3)),

    # SERIGNE AMADOU TOURE — VOLAILLE (Kaolack-Kaffrine)
    ("TOURE", "SERIGNE AMADOU", "SUD", Gamme.VOLAILLE,
     _mois([880, 820, 655, 820, 820, 690, 850, 880, 930, 1165], 3)),

    # ISMA BA — BETAIL (Ziguinchor)
    ("BA", "ISMA", "SUD", Gamme.BETAIL,
     _mois([365, 465, 485, 400, 400, 300, 300, 320, 340, 340], 3)),

    # ISMA BA — VOLAILLE (Ziguinchor)
    ("BA", "ISMA", "SUD", Gamme.VOLAILLE,
     _mois([1130, 1070, 905, 1070, 1070, 940, 1110, 1150, 1200, 1420], 3)),

    # ══ ZONE DAKAR ══════════════════════════════════════════════════════════
    # FATMA DIAGNE — FARINE (Plateau)
    ("DIAGNE", "FATMA", "DAKAR", Gamme.FARINE,
     _mois([1200, 1380, 1380, 1380, 1380, 1280, 1380, 1280, 1280, 1280, 1400, 1400], 1)),

    # MOUSSA KEBE — FARINE (Banlieue 1 ; total combiné − pâtes)
    ("KEBE", "MOUSSA", "DAKAR", Gamme.FARINE,
     _mois([835, 980, 980, 1050, 1050, 1040, 1000, 1040, 1040, 1000, 1080, 1080], 1)),

    # MOUSSA KEBE — PATES (Banlieue 1)
    ("KEBE", "MOUSSA", "DAKAR", Gamme.PATES,
     _mois([175, 230, 230, 160, 160, 120, 160, 120, 120, 160, 180, 180], 1)),

    # ANTA KONATE — PATES (Plateau)
    ("KONATE", "ANTA", "DAKAR", Gamme.PATES,
     _mois([125, 140, 140, 100, 100, 90, 100, 90, 90, 100, 120, 120], 1)),

    # DIARRA DIOP — PATES (Banlieue 2)
    ("DIOP", "DIARRA", "DAKAR", Gamme.PATES,
     _mois([100, 130, 130, 90, 90, 90, 90, 90, 90, 90, 100, 100], 1)),

    # MAMADOU DIAGNE — BETAIL (Plateau)
    ("DIAGNE", "MAMADOU", "DAKAR", Gamme.BETAIL,
     _mois([1300, 1200, 1250, 1800, 1700, 1500, 1500, 1250, 1200, 1200, 1250, 1250], 1)),

    # MAMADOU DIAGNE — VOLAILLE (Plateau)
    ("DIAGNE", "MAMADOU", "DAKAR", Gamme.VOLAILLE,
     _mois([1450, 1300, 1500, 1360, 1250, 1360, 1500, 1250, 1400, 1300, 1450, 1450], 1)),

    # EL H MANDOUMBE MBAYE — BETAIL (Banlieue 1)
    ("MBAYE", "EL H MANDOUMBE", "DAKAR", Gamme.BETAIL,
     _mois([1500, 1400, 1450, 2500, 2500, 2200, 2200, 1450, 1350, 1350, 1400, 1500], 1)),

    # EL H MANDOUMBE MBAYE — VOLAILLE (Banlieue 1)
    ("MBAYE", "EL H MANDOUMBE", "DAKAR", Gamme.VOLAILLE,
     _mois([2900, 2400, 2630, 2215, 2000, 2215, 2630, 2000, 2630, 2500, 2850, 2850], 1)),

    # IBRAHIMA FALL — BETAIL (Banlieue 2)
    ("FALL", "IBRAHIMA", "DAKAR", Gamme.BETAIL,
     _mois([400, 400, 400, 600, 600, 400, 400, 400, 350, 350, 350, 400], 1)),

    # IBRAHIMA FALL — VOLAILLE (Banlieue 2)
    ("FALL", "IBRAHIMA", "DAKAR", Gamme.VOLAILLE,
     _mois([2850, 2330, 2550, 2190, 1980, 2190, 2550, 1980, 2550, 2400, 2800, 2800], 1)),
]


def run():
    db = SessionLocal()
    try:
        regions = {r.nom: r for r in db.query(Region).all()}
        created = skipped = errors = 0

        for nom, prenom, region_nom, gamme, monthly in OBJECTIVES:
            region = regions.get(region_nom)
            if not region:
                print(f"  ✗  Région '{region_nom}' introuvable")
                errors += 1
                continue

            emp = db.query(Employee).filter(
                Employee.nom == nom,
                Employee.prenom == prenom,
                Employee.region_id == region.id,
            ).first()

            if not emp:
                print(f"  ✗  Employé introuvable : {prenom} {nom} / {region_nom}")
                errors += 1
                continue

            for periode, volume in monthly.items():
                if volume == 0:
                    continue
                exists = db.query(Objective).filter(
                    Objective.employee_id == emp.id,
                    Objective.periode == periode,
                    Objective.gamme == gamme,
                ).first()
                if exists:
                    exists.objectif_volume = volume
                    skipped += 1
                else:
                    db.add(Objective(
                        employee_id=emp.id,
                        periode=periode,
                        gamme=gamme,
                        objectif_volume=volume,
                    ))
                    created += 1

        db.commit()
        print(f"\n{'─'*60}")
        print(f"  {created} objectif(s) créé(s) | {skipped} mis à jour | {errors} erreur(s)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
