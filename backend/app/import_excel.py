"""
Import d'employés depuis un fichier Excel.
Format attendu des colonnes :
  NOM | PRENOM | TYPE_POSTE | REGION | SECTEUR | EMAIL | SAP_CODE | SF_ID

Types de poste valides :
  RCR, SV, COMMERCIAL, ATC_BV, ATC_FARINE, RCE, RESP_TECH_FP, RESP_TECH_BV, DV, DCMT

Usage :
  python -m app.import_excel chemin/vers/fichier.xlsx
"""
import sys
import pandas as pd
from .database import SessionLocal
from .models.employee import Employee, Region, TypePoste


def run(filepath: str):
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        print(f"Erreur lecture fichier : {e}")
        sys.exit(1)

    # Normaliser les noms de colonnes
    df.columns = [c.strip().upper() for c in df.columns]

    required = {"NOM", "PRENOM", "TYPE_POSTE", "REGION"}
    missing = required - set(df.columns)
    if missing:
        print(f"Colonnes manquantes : {missing}")
        print(f"Colonnes trouvées   : {list(df.columns)}")
        sys.exit(1)

    db = SessionLocal()
    try:
        regions = {r.nom: r for r in db.query(Region).all()}
        created = skipped = errors = 0

        for i, row in df.iterrows():
            nom        = str(row["NOM"]).strip().upper()
            prenom     = str(row["PRENOM"]).strip().upper()
            type_str   = str(row["TYPE_POSTE"]).strip().upper()
            region_nom = str(row["REGION"]).strip().upper()
            secteur    = str(row.get("SECTEUR", "")).strip() or None
            email      = str(row.get("EMAIL", "")).strip() or None
            sap_code   = str(row.get("SAP_CODE", "")).strip() or None
            sf_id      = str(row.get("SF_ID", "")).strip() or None

            # Valider type_poste
            try:
                type_poste = TypePoste(type_str)
            except ValueError:
                print(f"  ✗ Ligne {i+2} — type_poste invalide : '{type_str}'")
                errors += 1
                continue

            # Valider région
            region = regions.get(region_nom)
            if not region:
                print(f"  ✗ Ligne {i+2} — région introuvable : '{region_nom}'")
                errors += 1
                continue

            # Vérifier doublon
            exists = db.query(Employee).filter(
                Employee.nom == nom,
                Employee.prenom == prenom,
                Employee.region_id == region.id,
            ).first()

            if exists:
                print(f"  = {prenom} {nom} déjà présent")
                skipped += 1
                continue

            db.add(Employee(
                nom=nom, prenom=prenom,
                type_poste=type_poste,
                region_id=region.id,
                secteur=secteur,
                email=email,
                sap_code=sap_code,
                sf_id=sf_id,
                actif=True,
            ))
            print(f"  + {prenom} {nom} ({type_str} / {region_nom})")
            created += 1

        db.commit()
        print(f"\n✓ {created} créé(s) | {skipped} déjà présent(s) | {errors} erreur(s)")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python -m app.import_excel fichier.xlsx")
        sys.exit(1)
    run(sys.argv[1])
