from pydantic import BaseModel
from typing import Optional
from ..models.objective import Gamme


class ObjectiveBase(BaseModel):
    employee_id: int
    periode: str
    gamme: Gamme
    objectif_volume: Optional[float] = None
    objectif_ca: Optional[float] = None


class ObjectiveCreate(ObjectiveBase):
    pass


class ObjectiveUpdate(BaseModel):
    objectif_volume: Optional[float] = None
    objectif_ca: Optional[float] = None


class ObjectiveRead(ObjectiveBase):
    id: int
    model_config = {"from_attributes": True}


class SalesForecastBase(BaseModel):
    employee_id: int
    periode: str
    gamme: Gamme
    volume_prevu: Optional[float] = None
    ca_prevu: Optional[float] = None


class SalesForecastCreate(SalesForecastBase):
    pass


class SalesForecastRead(SalesForecastBase):
    id: int
    model_config = {"from_attributes": True}


class ClientBase(BaseModel):
    code_sap: str
    nom: str
    region_id: Optional[int] = None
    gamme_principale: Optional[Gamme] = None
    actif: bool = True


class ClientCreate(ClientBase):
    pass


class ClientRead(ClientBase):
    id: int
    model_config = {"from_attributes": True}


class PortfolioAssign(BaseModel):
    employee_id: int
    client_id: int
    annee: int
