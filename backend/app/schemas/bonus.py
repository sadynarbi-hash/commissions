from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from ..models.bonus import StatutBonus


class BonusPeriodRead(BaseModel):
    id: int
    periode: str
    statut: StatutBonus
    date_calcul: Optional[datetime] = None
    valide_par: Optional[str] = None
    date_validation: Optional[datetime] = None
    model_config = {"from_attributes": True}


class BonusQualDetailRead(BaseModel):
    id: int
    critere_code: str
    critere_libelle: str
    valeur_atteinte: Optional[str] = None
    seuil_requis: Optional[str] = None
    montant_max: float
    montant_accorde: float
    eligible: bool
    model_config = {"from_attributes": True}


class BonusRead(BaseModel):
    id: int
    employee_id: int
    period_id: int
    taux_atteinte_global: Optional[float] = None
    taux_atteinte_pates: Optional[float] = None
    taux_atteinte_autres: Optional[float] = None
    volume_realise: float = 0
    volume_objectif: float = 0
    nb_visites: int = 0
    prime_suivi_fixe: float
    prime_quantitative: float
    prime_qualitative: float
    commission_nouvelles_affaires: float
    total: float
    qualitative_eligible: bool
    statut: StatutBonus
    observations: Optional[str] = None
    calcule_le: datetime
    qual_details: list[BonusQualDetailRead] = []
    model_config = {"from_attributes": True}


class BonusCalculateRequest(BaseModel):
    periode: str
    employee_ids: Optional[list[int]] = None  # None = tous


class BonusValidateRequest(BaseModel):
    periode: str
    valide_par: str


class ManualCriteriaInput(BaseModel):
    employee_id: int
    periode: str
    critere_code: str
    valeur: bool
    notes: Optional[str] = None
    saisi_par: Optional[str] = None
