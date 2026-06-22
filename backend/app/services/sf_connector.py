from __future__ import annotations
"""
Connecteur Salesforce — OAuth 2.0 Client Credentials Flow (sans MFA).
"""
import logging
import requests
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)


class SalesforceConnector:
    def __init__(self, client_id: str, client_secret: str, domain: str = "login"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.domain = domain
        self._sf = None

    def _get_sf(self):
        if self._sf is None:
            # OAuth 2.0 Client Credentials — pas de MFA
            token_url = f"https://{self.domain}.salesforce.com/services/oauth2/token"
            resp = requests.post(token_url, data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            })
            resp.raise_for_status()
            data = resp.json()
            from simple_salesforce import Salesforce
            self._sf = Salesforce(
                session_id=data["access_token"],
                instance_url=data["instance_url"],
            )
        return self._sf

    def test_connection(self) -> bool:
        try:
            sf = self._get_sf()
            sf.query("SELECT Id FROM User LIMIT 1")
            return True
        except Exception as e:
            logger.error(f"Salesforce connection failed: {e}")
            return False

    def get_visits(self, date_from: date, date_to: date, sf_user_ids: list[str] | None = None) -> list[dict]:
        """Retourne les lignes de visite Salesforce (VisiteLine__c) pour la période.

        On compte les VisiteLine__c (un client visité = une ligne) comme Power BI.
        Filtre par Datedone__c si la tournée est clôturée, sinon Predicted_date__c.
        """
        user_filter = ""
        if sf_user_ids:
            ids = ",".join([f"'{uid}'" for uid in sf_user_ids])
            user_filter = f"AND Visite_id__r.OwnerId IN ({ids})"

        df = date_from.isoformat()
        dt = date_to.isoformat()
        soql = f"""
            SELECT
                Id,
                Visite_id__c,
                Visite_id__r.OwnerId,
                Visite_id__r.Datedone__c,
                Visite_id__r.Predicted_date__c,
                Visite_id__r.State__c,
                Account__c,
                Account__r.Name,
                Account__r.SAP_Customer_Number__c,
                Division__c,
                date_de_visite__c
            FROM VisiteLine__c
            WHERE Account__c != null
            AND date_de_visite__c >= {df}
            AND date_de_visite__c <= {dt}
            {user_filter}
        """
        try:
            sf = self._get_sf()
            result = sf.query_all(soql)
            return result.get("records", [])
        except Exception as e:
            logger.error(f"Salesforce get_visits failed: {e}")
            return []

    def get_crm_compliance(self, date_from: date, date_to: date,
                           sf_user_ids: list[str] | None = None) -> list[dict]:
        user_filter = ""
        if sf_user_ids:
            ids = ",".join([f"'{uid}'" for uid in sf_user_ids])
            user_filter = f"AND OwnerId IN ({ids})"

        soql = f"""
            SELECT OwnerId, COUNT(Id) total_activities
            FROM Task
            WHERE ActivityDate >= {date_from.isoformat()}
              AND ActivityDate <= {date_to.isoformat()}
              {user_filter}
            GROUP BY OwnerId
        """
        try:
            sf = self._get_sf()
            result = sf.query_all(soql)
            return result.get("records", [])
        except Exception as e:
            logger.error(f"Salesforce get_crm_compliance failed: {e}")
            return []

    def get_reports_submitted(self, date_from: date, date_to: date,
                              sf_user_ids: list[str] | None = None) -> list[dict]:
        user_filter = ""
        if sf_user_ids:
            ids = ",".join([f"'{uid}'" for uid in sf_user_ids])
            user_filter = f"AND OwnerId IN ({ids})"

        soql = f"""
            SELECT Id, OwnerId, Subject, ActivityDate, Type, Status
            FROM Task
            WHERE ActivityDate >= {date_from.isoformat()}
              AND ActivityDate <= {date_to.isoformat()}
              AND Type IN ('Report', 'Planning', 'Rapport')
              AND Status = 'Completed'
              {user_filter}
        """
        try:
            sf = self._get_sf()
            result = sf.query_all(soql)
            return result.get("records", [])
        except Exception as e:
            logger.error(f"Salesforce get_reports_submitted failed: {e}")
            return []


def get_sf_connector(settings) -> "SalesforceConnector | None":
    if not settings.SF_CLIENT_ID:
        return None
    return SalesforceConnector(
        client_id=settings.SF_CLIENT_ID,
        client_secret=settings.SF_CLIENT_SECRET,
        domain=settings.SF_DOMAIN,
    )
