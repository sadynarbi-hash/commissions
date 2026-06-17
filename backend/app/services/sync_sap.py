from __future__ import annotations
"""
Service de synchronisation SAP B1 → base locale.
Agrège les BL (ODLN/DLN1) par commercial + gamme + période.
Synchronise également le portefeuille clients (OCRD) et les volumes
par client (courant + N-1) pour le calcul des critères qualitatifs.
"""
from datetime import date
from decimal import Decimal
from typing import Optional
import logging

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..models.employee import Employee
from ..models.sales import SaleData, SyncLog, SyncSourceType, SyncStatut
from ..models.objective import Gamme, Client, ClientPortfolio, ClientMonthlySale
from ..models.geography import Zone, SecteurGeo, Secteur
from ..services.sap_connector import SAPConnectorBase

logger = logging.getLogger(__name__)

KG_TO_TONNE = Decimal("1000")


def sync_sales(db: Session, connector: SAPConnectorBase,
               date_from: date, date_to: date | None = None) -> dict:
    """
    Tire les BL SAP, filtre les produits finis (PF*),
    agrège par (sap_code, gamme, période) et stocke dans sales_data.
    """
    periode = date_from.strftime("%Y-%m")
    log = SyncLog(source=SyncSourceType.SAP, periode=periode,
                  statut=SyncStatut.EN_COURS)
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        rows = connector.get_sales(date_from, date_to)

        # Index employés par sap_code (int ou str)
        all_emps = db.query(Employee).filter(Employee.sap_code.isnot(None)).all()
        employes = {str(e.sap_code): e for e in all_emps}
        emp_export = next((e for e in all_emps if e.sap_code == "__export__"), None)

        # Alias : anciens codes SAP → employé actif correspondant
        SAP_ALIASES = {"24": "32"}  # ALASSANE WADE ancien code → code actif
        for alias, target in SAP_ALIASES.items():
            if target in employes:
                employes[alias] = employes[target]

        # Supprimer les enregistrements du mois courant AVANT réinsertion
        # (évite les données périmées de l'ancienne méthode SlpCode)
        emp_ids = [e.id for e in employes.values()]
        if emp_ids:
            db.query(SaleData).filter(
                SaleData.periode == periode,
                SaleData.employee_id.in_(emp_ids),
            ).delete(synchronize_session=False)
            db.flush()

        # Agrégation BL : {(sap_code, gamme, periode) -> {volume_kg, montant}}
        # + agrégation client : {(sap_code, client_code) -> {volume_kg, client_nom}}
        agg: dict[tuple, dict] = {}
        client_agg: dict[tuple, dict] = {}   # (sap_code, client_code) -> volume

        skipped_no_emp = 0

        for r in rows:
            code_article = str(r.get("article_code", "") or "")
            gamme_str    = connector.detect_gamme(code_article)
            # Ignorer négoce (PFNE) — seuls les PF* hors PFNE sont des produits finis
            if code_article.upper().startswith('PFNE'):
                continue

            sap_code = str(r.get("sap_code_employe", "") or "")
            emp      = employes.get(sap_code)
            if not emp:
                if emp_export:
                    emp      = emp_export
                    sap_code = "__export__"
                else:
                    skipped_no_emp += 1
                    continue
            # Normaliser vers le code canonique (gère les alias ex: 24→32)
            sap_code = str(emp.sap_code)

            poids   = Decimal(str(r.get("poids_kg") or 0))
            montant = Decimal(str(r.get("montant_ht") or 0))

            # Période réelle du bon de livraison (pas date_from)
            date_bl = r.get("date_livraison")
            periode_bl = date_bl.strftime("%Y-%m") if date_bl else periode

            key = (sap_code, gamme_str, periode_bl)
            if key not in agg:
                agg[key] = {"employee": emp, "volume_kg": Decimal(0),
                            "montant": Decimal(0), "date_ref": date_bl or date_from}
            agg[key]["volume_kg"] += poids
            agg[key]["montant"]   += montant

            # Agrégation par client (toutes gammes confondues)
            client_code = str(r.get("client_code") or "")
            if client_code:
                ck = (sap_code, client_code, periode_bl)
                if ck not in client_agg:
                    client_agg[ck] = {
                        "employee": emp,
                        "client_nom": r.get("client_nom") or "",
                        "volume_kg": Decimal(0),
                        "montant": Decimal(0),
                    }
                client_agg[ck]["volume_kg"] += poids
                client_agg[ck]["montant"] += montant

        # Insérer les nouvelles données (DELETE déjà fait au-dessus)
        created = updated = 0
        for (sap_code, gamme_str, per), data in agg.items():
            emp    = data["employee"]
            gamme  = Gamme(gamme_str)
            volume = data["volume_kg"] / KG_TO_TONNE   # kg → tonnes
            source = f"SAP-{per}-{sap_code}-{gamme_str}"

            existing = db.query(SaleData).filter(SaleData.source_id == source).first()
            if existing:
                existing.volume          = float(volume)
                existing.montant_ht      = float(data["montant"])
                updated += 1
            else:
                db.add(SaleData(
                    source_id       = source,
                    employee_id     = emp.id,
                    gamme           = gamme,
                    volume          = float(volume),
                    montant_ht      = float(data["montant"]),
                    montant_recouvre= 0,
                    date_facture    = data["date_ref"],
                    periode         = per,
                ))
                created += 1

        db.commit()

        # ── CA mois M + Recouvrement mois M-1 (règle métier NMA) ────────
        # Bonus de mois M = CA(M) mais taux recouvrement = MontantPayé(M-1)/CA(M-1)
        # On synce donc les deux périodes pour avoir M-1 à jour au moment du calcul
        from calendar import monthrange as _mr2
        mois_m = date_from.month
        annee_m = date_from.year
        if mois_m == 1:
            date_m1_from = date(annee_m - 1, 12, 1)
        else:
            date_m1_from = date(annee_m, mois_m - 1, 1)
        date_m1_to = date_m1_from.replace(
            day=_mr2(date_m1_from.year, date_m1_from.month)[1]
        )

        # Collections M (CA courant)
        collections = connector.get_collections(date_from, date_to)
        # Collections M-1 (recouvrement à jour pour la règle M-1)
        collections_m1 = connector.get_collections(date_m1_from, date_m1_to)

        # Agréger par (emp_id, periode) : CA net + MontantPaye — M et M-1
        recouv_agg: dict[tuple, dict] = {}
        for r in list(collections) + list(collections_m1):
            sap_code = str(r.get("sap_code_employe", "") or "")
            emp      = employes.get(sap_code)
            if not emp:
                continue
            per_col  = str(r.get("periode") or periode)[:7]
            key      = (emp.id, per_col)
            if key not in recouv_agg:
                recouv_agg[key] = {"facture": 0.0, "recouvre": 0.0}
            recouv_agg[key]["facture"]  += float(r.get("montant_facture")  or 0)
            recouv_agg[key]["recouvre"] += float(r.get("montant_recouvre") or 0)

        # Mise à jour montant_ht + montant_recouvre sur SaleData — prorata CA par gamme
        recouv_updated = 0
        for (emp_id, per_enc), totaux in recouv_agg.items():
            total_ca_col   = totaux["facture"]
            total_recouv   = totaux["recouvre"]
            sales_rows = db.query(SaleData).filter(
                SaleData.employee_id == emp_id,
                SaleData.periode     == per_enc,
            ).all()
            if not sales_rows:
                continue
            taux_recouv = total_recouv / total_ca_col if total_ca_col > 0 else 0
            for s in sales_rows:
                s.montant_recouvre = float(s.montant_ht or 0) * taux_recouv
            recouv_updated += len(sales_rows)

        db.commit()

        # ── Volumes clients mois courant → ClientMonthlySale ─────────────
        cms_upserted = 0
        for (sap_code, client_code, per), data in client_agg.items():
            emp       = data["employee"]
            volume    = float(data["volume_kg"] / KG_TO_TONNE)
            montant_c = float(data["montant"])
            existing = db.query(ClientMonthlySale).filter(
                ClientMonthlySale.employee_id == emp.id,
                ClientMonthlySale.client_code == client_code,
                ClientMonthlySale.periode     == per,
                ClientMonthlySale.annee_n1    == False,
            ).first()
            if existing:
                existing.volume     = volume
                existing.montant_ca = montant_c
                existing.client_nom = data["client_nom"]
            else:
                db.add(ClientMonthlySale(
                    employee_id = emp.id,
                    client_code = client_code,
                    client_nom  = data["client_nom"],
                    periode     = per,
                    volume      = volume,
                    montant_ca  = montant_c,
                    annee_n1    = False,
                ))
            cms_upserted += 1
        db.commit()

        # ── Volumes clients mois N-1 → ClientMonthlySale (annee_n1=True) ─
        from calendar import monthrange as _mr
        annee_sync = date_from.year
        mois_sync  = date_from.month
        date_n1_from = date(annee_sync - 1, mois_sync, 1)
        date_n1_to   = date(annee_sync - 1, mois_sync, _mr(annee_sync - 1, mois_sync)[1])
        periode_n1   = date_n1_from.strftime("%Y-%m")

        rows_n1 = connector.get_sales(date_n1_from, date_n1_to)
        n1_agg: dict[tuple, dict] = {}
        for r in rows_n1:
            code_article = str(r.get("article_code", "") or "")
            if not connector.detect_gamme(code_article):
                continue
            sap_code    = str(r.get("sap_code_employe", "") or "")
            emp         = employes.get(sap_code)
            client_code = str(r.get("client_code") or "")
            if not emp or not client_code:
                continue
            poids = Decimal(str(r.get("poids_kg") or 0))
            ck = (emp.id, client_code)
            if ck not in n1_agg:
                n1_agg[ck] = {"client_nom": r.get("client_nom") or "", "volume_kg": Decimal(0)}
            n1_agg[ck]["volume_kg"] += poids

        n1_upserted = 0
        for (emp_id, client_code), data in n1_agg.items():
            volume = float(data["volume_kg"] / KG_TO_TONNE)
            existing = db.query(ClientMonthlySale).filter(
                ClientMonthlySale.employee_id == emp_id,
                ClientMonthlySale.client_code == client_code,
                ClientMonthlySale.periode     == periode_n1,
                ClientMonthlySale.annee_n1    == True,
            ).first()
            if existing:
                existing.volume = volume
            else:
                db.add(ClientMonthlySale(
                    employee_id = emp_id,
                    client_code = client_code,
                    client_nom  = data["client_nom"],
                    periode     = periode_n1,
                    volume      = volume,
                    annee_n1    = True,
                ))
            n1_upserted += 1
        db.commit()

        # ── Portefeuille clients depuis OCRD → Client + ClientPortfolio ──
        sap_codes_list = [str(e.sap_code) for e in employes.values()
                          if e.sap_code and e.sap_code != "__export__"]
        portfolio_rows = connector.get_portfolio_all(sap_codes_list)

        annee_sync_int = annee_sync
        portefeuille_updated = 0
        for r in portfolio_rows:
            sap_code    = str(r.get("sap_code_employe", "") or "")
            emp         = employes.get(sap_code)
            client_code = str(r.get("client_code") or "")
            if not emp or not client_code:
                continue

            # Upsert Client
            client = db.query(Client).filter(Client.code_sap == client_code).first()
            date_ouv = r.get("date_ouverture")
            if hasattr(date_ouv, "date"):
                date_ouv = date_ouv.date()
            if not client:
                client = Client(code_sap=client_code, nom=r.get("client_nom") or client_code,
                                date_ouverture=date_ouv)
                db.add(client)
                db.flush()
            else:
                client.nom = r.get("client_nom") or client.nom
                if date_ouv and not client.date_ouverture:
                    client.date_ouverture = date_ouv

            # Upsert ClientPortfolio (remplace si le commercial change de secteur)
            existing_p = db.query(ClientPortfolio).filter(
                ClientPortfolio.client_id == client.id,
                ClientPortfolio.annee     == annee_sync_int,
            ).first()
            if existing_p:
                if existing_p.employee_id != emp.id:
                    existing_p.employee_id = emp.id   # changement de secteur
            else:
                db.add(ClientPortfolio(
                    employee_id = emp.id,
                    client_id   = client.id,
                    annee       = annee_sync_int,
                ))
            portefeuille_updated += 1

        db.commit()

        nb = created + updated
        log.statut     = SyncStatut.SUCCES
        log.nb_records = nb
        log.message    = (f"{created} créés, {updated} màj, {recouv_updated} recouv. "
                          f"Portefeuille: {portefeuille_updated} clients. "
                          f"Volumes clients: {cms_upserted} courant, {n1_upserted} N-1. "
                          f"Ignorés: {skipped_no_emp} (vendeur)")
        db.commit()

        logger.info(f"Sync SAP OK — {nb} agrégats, {skipped_no_emp} vendeurs SAP sans correspondance")
        return {"created": created, "updated": updated, "skipped_emp": skipped_no_emp}

    except Exception as e:
        log.statut  = SyncStatut.ERREUR
        log.message = str(e)
        db.commit()
        logger.error(f"Sync SAP erreur: {e}")
        raise


def sync_geography(db: Session, connector: SAPConnectorBase) -> dict:
    """
    Synchronise zones, secteurs géographiques, secteurs commerciaux
    et le champ U_Secteur de chaque client depuis SAP.
    À appeler indépendamment de sync_sales (les données géo changent rarement).
    """
    # ── Index employés par nom partiel (pour matcher les noms tronqués SAP) ──
    employes_list = db.query(Employee).filter(Employee.actif == True).all()

    def find_employee(nom_sap: str) -> Optional[int]:
        """Matche un nom SAP (potentiellement tronqué) à un employé local.
        Priorité : exact → SAP contenu dans nom complet → nom contenu dans SAP.
        Pas de match sur préfixe court pour éviter les faux positifs (ex: FATMA AMAR ≠ FATMA DIAGNE).
        """
        if not nom_sap:
            return None
        nom_up = nom_sap.strip().upper()
        # 1. Correspondance exacte
        for e in employes_list:
            if f"{e.prenom} {e.nom}".upper() == nom_up:
                return e.id
        # 2. Nom SAP (tronqué) contenu dans le nom complet local — ex: "FATMA DIA" in "FATMA DIAGNE"
        for e in employes_list:
            if nom_up in f"{e.prenom} {e.nom}".upper():
                return e.id
        # 3. Nom local contenu dans le nom SAP — ex: "ISMA BA" in "ISMA BA DIALLO"
        for e in employes_list:
            if f"{e.prenom} {e.nom}".upper() in nom_up:
                return e.id
        return None

    # ── 1. Zones (@ZONESLIGNES) ───────────────────────────────────────────
    zones_rows = connector.get_zones()
    zones_count = 0
    for r in zones_rows:
        code = str(r.get("code") or "").strip()
        nom  = str(r.get("nom") or "").strip()
        if not code:
            continue
        zone = db.query(Zone).filter(Zone.code == code).first()
        if not zone:
            zone = Zone(code=code, nom=nom)
            db.add(zone)
        else:
            zone.nom = nom
        zone.superviseur_id = find_employee(r.get("superviseur_nom"))
        zone.responsable_id = find_employee(r.get("responsable_nom"))
        zone.docteur_id     = find_employee(r.get("docteur_nom"))
        zones_count += 1
    db.flush()

    # Index zones par code
    zones_by_code = {z.code: z for z in db.query(Zone).all()}

    # ── 2. Secteurs géographiques (@SECTEURSLIGNE) ────────────────────────
    geo_rows = connector.get_secteurs_geo()
    geo_count = 0
    for r in geo_rows:
        code      = str(r.get("code") or "").strip()
        nom       = str(r.get("nom") or "").strip()
        zone_code = str(r.get("zone_code") or "").strip()
        if not code:
            continue
        zone = zones_by_code.get(zone_code)
        sg = db.query(SecteurGeo).filter(SecteurGeo.code == code).first()
        if not sg:
            sg = SecteurGeo(code=code, nom=nom, zone_id=zone.id if zone else None)
            db.add(sg)
        else:
            sg.nom     = nom
            sg.zone_id = zone.id if zone else sg.zone_id
        geo_count += 1
    db.flush()

    # ── 3. Secteurs commerciaux (@COMSECTEURLIGNE) ────────────────────────
    com_rows = connector.get_secteurs_commerciaux()
    com_count = 0
    for r in com_rows:
        code         = str(r.get("code") or "").strip()           # Z1S1BV
        geo_code     = str(r.get("secteur_geo_code") or "").strip()
        gamme        = str(r.get("gamme") or "").strip()
        commercial   = r.get("commercial_nom")
        docteur      = r.get("docteur_nom")
        if not code:
            continue
        sec = db.query(Secteur).filter(Secteur.code == code).first()
        if not sec:
            sec = Secteur(code=code, gamme=gamme, secteur_geo_code=geo_code)
            db.add(sec)
        else:
            sec.gamme            = gamme
            sec.secteur_geo_code = geo_code
        # employee_id depuis U_RESPONSABLE — toujours mis à jour depuis SAP
        emp_id = find_employee(commercial)
        if emp_id is not None:
            sec.employee_id = emp_id
        sec.docteur_id = find_employee(docteur)
        com_count += 1
    db.flush()

    # ── 4. Clients : U_Secteur + groupe depuis OCRD ───────────────────────
    u_sec_rows = connector.get_clients_u_secteur()
    u_sec_count = 0
    for r in u_sec_rows:
        client_code = str(r.get("client_code") or "")
        u_secteur   = str(r.get("u_secteur") or "").strip()
        client_nom  = str(r.get("client_nom") or "")
        if not client_code or not u_secteur:
            continue
        client = db.query(Client).filter(Client.code_sap == client_code).first()
        if not client:
            client = Client(code_sap=client_code, nom=client_nom)
            db.add(client)
        else:
            if client_nom:
                client.nom = client_nom
        if client.u_secteur != u_secteur:
            client.u_secteur = u_secteur
            u_sec_count += 1

    db.commit()
    logger.info(f"Sync géographie OK — {zones_count} zones, {geo_count} secteurs geo, "
                f"{com_count} secteurs commerciaux, {u_sec_count} clients màj")
    return {
        "zones": zones_count,
        "secteurs_geo": geo_count,
        "secteurs_commerciaux": com_count,
        "clients_u_secteur": u_sec_count,
    }
