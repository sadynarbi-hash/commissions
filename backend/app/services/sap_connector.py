from __future__ import annotations
"""
Connecteur SAP B1 — supporte SQL Server (pyodbc) et HANA (hdbcli).
Extrait ventes, recouvrement et portefeuille clients.
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import Any
import logging

logger = logging.getLogger(__name__)


class SAPConnectorBase(ABC):
    @abstractmethod
    def get_connection(self): ...

    @abstractmethod
    def test_connection(self) -> bool: ...

    def execute_query(self, sql: str, params: tuple = ()) -> list[dict]:
        # pymssql utilise %s comme placeholder (pas ?)
        sql_adapted = sql.replace("?", "%s")
        conn = self.get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql_adapted, params)
            return cursor.fetchall()
        finally:
            conn.close()

    # ── Détection gamme depuis code article ───────────────
    @staticmethod
    def detect_gamme(article_code: str) -> str:
        prefix = article_code[:4].upper()
        return {
            'PFBE': 'BETAIL',
            'PFFA': 'FARINE',
            'PFPA': 'PATES',
            'PFVO': 'VOLAILLE',
        }.get(prefix, 'AUTRES')

    # ── Requêtes métier ────────────────────────────────────
    def get_sales(self, date_from: date, date_to: date | None = None, sap_codes: list[str] | None = None) -> list[dict]:
        """Retourne les bons de livraison SAP B1 (ODLN/DLN1) pour la période.
        Attribution via OCRD.U_Secteur → @COMSECTEURLIGNE.U_OSLP (cohérent avec Power BI).
        """
        from calendar import monthrange
        if date_to is None:
            last_day = monthrange(date_from.year, date_from.month)[1]
            date_to = date_from.replace(day=last_day)

        codes_filter = ""
        params: list[Any] = [date_from.isoformat(), date_to.isoformat()]
        if sap_codes:
            placeholders = ",".join(["?" for _ in sap_codes])
            codes_filter = f"AND E.U_OSLP IN ({placeholders})"
            params.extend(sap_codes)

        sql = f"""
            SELECT
                CAST(T0.DocNum AS VARCHAR(20))  AS source_id,
                E.U_OSLP                        AS sap_code_employe,
                T0.DocDate                      AS date_livraison,
                T0.CardCode                     AS client_code,
                T0.CardName                     AS client_nom,
                T0.UserSign                     AS utilisateur,
                T1.ItemCode                     AS article_code,
                T1.Dscription                   AS article_nom,
                T1.Quantity                     AS quantite,
                T1.Price                        AS prix_unitaire,
                T1.TotalSumSy                   AS montant_ht,
                T1.Weight1                      AS poids_kg,
                T1.UomCode                      AS unite
            FROM ODLN T0
            INNER JOIN DLN1 T1  ON T0.DocEntry  = T1.DocEntry
            INNER JOIN OCRD C   ON T0.CardCode  = C.CardCode
            INNER JOIN [@COMSECTEURLIGNE] E ON C.U_Secteur = E.U_CODE
            WHERE T0.Canceled = 'N'
              AND T0.DocDate BETWEEN ? AND ?
              AND T1.ItemCode LIKE 'PF%'
              AND T1.ItemCode NOT LIKE 'PFNE%'
              {codes_filter}
            ORDER BY T0.DocDate
        """
        return self.execute_query(sql, tuple(params))

    def get_collections(self, date_from: date, date_to: date | None = None) -> list[dict]:
        """
        CA et recouvrement par client — logique identique à Power BI Reporting NMA.

        OINV/INV1 (factures)  : CA positif,  MontantPaye positif
        ORIN/RIN1 (avoirs)    : CA négatif,  MontantPaye négatif

        CA          = LineTotal × (1 − DiscPrcnt/100)   par ligne
        MontantPaye = CA × (PaidToDate / DocTotal)       prorata paiement par facture
                    OU CA entier si DocStatus='C'         (lettrée via OC/réconciliation)

        Agrégé par (CardCode, SlpCode, période mensuelle).
        """
        from calendar import monthrange
        if date_to is None:
            last_day = monthrange(date_from.year, date_from.month)[1]
            date_to = date_from.replace(day=last_day)

        # Commercial retrouvé via OCRD.U_Secteur → @COMSECTEURLIGNE → OSLP
        # (pas via OINV.SlpCode qui peut différer du responsable réel du client)
        sql = """
            SELECT
                T1.CardCode                                 AS client_code,
                E.U_OSLP                                    AS sap_code_employe,
                E.U_RESPONSABLE                             AS commercial_nom,
                CONVERT(VARCHAR(7), T1.DocDate, 120)        AS periode,
                T0.LineTotal * (1 - T1.DiscPrcnt / 100.0)  AS CA,
                CASE
                    WHEN T1.DocStatus = 'C'
                        THEN T0.LineTotal * (1 - T1.DiscPrcnt / 100.0)
                    ELSE T0.LineTotal * (1 - T1.DiscPrcnt / 100.0)
                        * ISNULL(T1.PaidToDate / NULLIF(T1.DocTotal, 0), 0)
                END AS MontantPaye
            FROM INV1 T0
            INNER JOIN OINV T1                ON T0.DocEntry = T1.DocEntry
            INNER JOIN OCRD C                 ON T1.CardCode = C.CardCode
            INNER JOIN [@COMSECTEURLIGNE] E   ON C.U_Secteur = E.U_CODE
            WHERE T1.CANCELED = 'N'
              AND T1.DocDate BETWEEN ? AND ?

            UNION ALL

            SELECT
                T1.CardCode,
                E.U_OSLP,
                E.U_RESPONSABLE,
                CONVERT(VARCHAR(7), T1.DocDate, 120),
                -(T0.LineTotal * (1 - T1.DiscPrcnt / 100.0)),
                CASE
                    WHEN T1.DocStatus = 'C'
                        THEN -(T0.LineTotal * (1 - T1.DiscPrcnt / 100.0))
                    ELSE -(T0.LineTotal * (1 - T1.DiscPrcnt / 100.0)
                        * ISNULL(T1.PaidToDate / NULLIF(T1.DocTotal, 0), 0))
                END
            FROM RIN1 T0
            INNER JOIN ORIN T1                ON T0.DocEntry = T1.DocEntry
            INNER JOIN OCRD C                 ON T1.CardCode = C.CardCode
            INNER JOIN [@COMSECTEURLIGNE] E   ON C.U_Secteur = E.U_CODE
            WHERE T1.CANCELED = 'N'
              AND T1.DocDate BETWEEN ? AND ?
        """
        sql_agg = f"""
            SELECT
                client_code,
                sap_code_employe,
                commercial_nom,
                periode,
                SUM(CA)           AS montant_facture,
                SUM(MontantPaye)  AS montant_recouvre
            FROM ({sql}) base
            GROUP BY client_code, sap_code_employe, commercial_nom, periode
            HAVING SUM(CA) <> 0
            ORDER BY sap_code_employe, client_code
        """
        params = (date_from.isoformat(), date_to.isoformat(),
                  date_from.isoformat(), date_to.isoformat())
        conn = self.get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(sql_agg.replace("?", "%s"), params)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_clients_portfolio(self, sap_code_employe: str) -> list[dict]:
        """Retourne les clients affectés à un commercial."""
        sql = """
            SELECT
                T0.CardCode AS client_code,
                T0.CardName AS client_nom,
                T0.SlpCode  AS sap_code_employe,
                T0.Active   AS actif
            FROM OCRD T0
            WHERE T0.SlpCode = ?
              AND T0.CardType = 'C'
            ORDER BY T0.CardName
        """
        return self.execute_query(sql, (sap_code_employe,))

    def get_portfolio_all(self, sap_codes: list[str]) -> list[dict]:
        """Retourne tous les clients pour une liste de commerciaux (OCRD.SlpCode).
        Quand un commercial change de secteur, seul son SlpCode change dans SAP —
        la prochaine sync reconstruit automatiquement le portefeuille.
        """
        if not sap_codes:
            return []
        placeholders = ",".join(["?" for _ in sap_codes])
        sql = f"""
            SELECT
                T0.CardCode   AS client_code,
                T0.CardName   AS client_nom,
                T0.SlpCode    AS sap_code_employe,
                T0.CreateDate AS date_ouverture
            FROM OCRD T0
            WHERE T0.SlpCode IN ({placeholders})
              AND T0.CardType = 'C'
              AND T0.validFor = 'Y'
            ORDER BY T0.SlpCode, T0.CardName
        """
        return self.execute_query(sql, tuple(sap_codes))

    def get_sales_n1(self, annee_n1: int, sap_codes: list[str] | None = None) -> list[dict]:
        """Retourne les volumes N-1 par client et commercial."""
        codes_filter = ""
        params: list[Any] = [f"{annee_n1}-01-01", f"{annee_n1}-12-31"]
        if sap_codes:
            placeholders = ",".join(["?" for _ in sap_codes])
            codes_filter = f"AND T0.SlpCode IN ({placeholders})"
            params.extend(sap_codes)

        sql = f"""
            SELECT
                T0.SlpCode    AS sap_code_employe,
                T0.CardCode   AS client_code,
                SUM(T1.Quantity) AS volume_total,
                SUM(T1.LineTotal) AS ca_total
            FROM OINV T0
            INNER JOIN INV1 T1 ON T0.DocEntry = T1.DocEntry
            WHERE T0.DocDate BETWEEN ? AND ?
              AND T0.CANCELED = 'N'
              {codes_filter}
            GROUP BY T0.SlpCode, T0.CardCode
        """
        return self.execute_query(sql, tuple(params))

    def get_zones(self) -> list[dict]:
        """Sync @ZONESLIGNES → zones locales."""
        sql = """
            SELECT
                U_Codez         AS code,
                U_ZONE          AS nom,
                U_Superviseur   AS superviseur_nom,
                U_RESPONSABLEREG AS responsable_nom,
                U_DOCTEUR       AS docteur_nom
            FROM [@ZONESLIGNES]
            ORDER BY U_Codez
        """
        return self.execute_query(sql)

    def get_secteurs_geo(self) -> list[dict]:
        """Sync @SECTEURSLIGNE → secteurs géographiques (sans gamme ni commercial)."""
        sql = """
            SELECT
                G.U_CODESEC     AS code,
                G.U_SECTEUR     AS nom,
                G.U_ZONE        AS zone_code
            FROM [@SECTEURSLIGNE] G
            ORDER BY G.U_CODESEC
        """
        return self.execute_query(sql)

    def get_secteurs_commerciaux(self) -> list[dict]:
        """Sync @COMSECTEURLIGNE → secteurs commerciaux avec gamme et commercial assigné.
        E.U_CODE = valeur de OCRD.U_Secteur sur les clients.
        """
        sql = """
            SELECT
                E.U_CODE            AS code,
                E.U_SECTEUR         AS nom,
                E.U_GAMME           AS gamme,
                E.U_CODESEC         AS secteur_geo_code,
                E.U_RESPONSABLE     AS commercial_nom,
                G.U_ZONE            AS zone_code,
                F.U_Superviseur     AS superviseur_nom,
                F.U_RESPONSABLEREG  AS responsable_nom,
                F.U_DOCTEUR         AS docteur_nom
            FROM [@COMSECTEURLIGNE] E
            INNER JOIN [@SECTEURSLIGNE] G ON E.U_CODESEC = G.U_CODESEC
            INNER JOIN [@ZONESLIGNES]   F ON G.U_ZONE    = F.U_Codez
            ORDER BY E.U_CODE
        """
        return self.execute_query(sql)

    def get_clients_u_secteur(self) -> list[dict]:
        """Retourne les clients avec leur secteur, zone et groupe depuis SAP.
        Lien : OCRD.U_Secteur = @COMSECTEURLIGNE.U_CODE
        """
        sql = """
            SELECT
                D.CardCode          AS client_code,
                D.CardName          AS client_nom,
                D.U_Secteur         AS u_secteur,
                E.U_SECTEUR         AS secteur_nom,
                E.U_GAMME           AS gamme,
                E.U_RESPONSABLE     AS commercial_nom,
                F.U_ZONE            AS zone_nom,
                F.U_Superviseur     AS superviseur_nom,
                F.U_RESPONSABLEREG  AS responsable_nom,
                H.GroupName         AS groupe_client
            FROM OCRD D
            INNER JOIN [@COMSECTEURLIGNE] E ON D.U_Secteur     = E.U_CODE
            INNER JOIN [@SECTEURSLIGNE]   G ON E.U_CODESEC     = G.U_CODESEC
            INNER JOIN [@ZONESLIGNES]     F ON G.U_ZONE        = F.U_Codez
            INNER JOIN OCRG               H ON D.GroupCode     = H.GroupCode
            WHERE D.CardType = 'C'
              AND D.validFor  = 'Y'
            ORDER BY E.U_RESPONSABLE
        """
        return self.execute_query(sql)

    def get_employees(self) -> list[dict]:
        """Retourne les commerciaux depuis la table des vendeurs SAP."""
        sql = """
            SELECT
                T0.SlpCode AS sap_code,
                T0.SlpName AS nom_complet,
                T0.Active  AS actif
            FROM OSLP T0
            ORDER BY T0.SlpName
        """
        return self.execute_query(sql)


class SAPSQLServerConnector(SAPConnectorBase):
    def __init__(self, server: str, database: str, username: str,
                 password: str, port: int = 1433, driver: str = ""):
        self.server   = server
        self.database = database
        self.username = username
        self.password = password
        self.port     = port

    def get_connection(self):
        import pymssql
        return pymssql.connect(
            server=self.server,
            port=self.port,
            user=self.username,
            password=self.password,
            database=self.database,
            tds_version="7.0",
        )

    def test_connection(self) -> bool:
        try:
            conn = self.get_connection()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"SAP SQL Server connection failed: {e}")
            return False


class SAPHANAConnector(SAPConnectorBase):
    def __init__(self, host: str, port: int, user: str, password: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    def get_connection(self):
        from hdbcli import dbapi
        return dbapi.connect(address=self.host, port=self.port,
                             user=self.user, password=self.password)

    def test_connection(self) -> bool:
        try:
            conn = self.get_connection()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"SAP HANA connection failed: {e}")
            return False


def get_sap_connector(settings) -> SAPConnectorBase | None:
    """Factory — retourne le bon connecteur selon la config."""
    if not settings.SAP_SERVER:
        return None
    if settings.SAP_DB_TYPE == "hana":
        return SAPHANAConnector(
            host=settings.SAP_HANA_HOST,
            port=settings.SAP_HANA_PORT,
            user=settings.SAP_HANA_USER,
            password=settings.SAP_HANA_PASSWORD,
        )
    return SAPSQLServerConnector(
        server=settings.SAP_SERVER,
        database=settings.SAP_DATABASE,
        username=settings.SAP_USERNAME,
        password=settings.SAP_PASSWORD,
        port=settings.SAP_PORT,
        driver=settings.SAP_DRIVER,
    )
