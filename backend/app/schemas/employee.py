from pydantic import BaseModel, EmailStr
from typing import Optional
from ..models.employee import TypePoste, TypeRegion


class RegionBase(BaseModel):
    nom: str
    type: TypeRegion = TypeRegion.NATIONALE


class RegionCreate(RegionBase):
    pass


class RegionRead(RegionBase):
    id: int
    model_config = {"from_attributes": True}


class EmployeeBase(BaseModel):
    nom: str
    prenom: str
    email: Optional[str] = None
    type_poste: TypePoste
    region_id: Optional[int] = None
    secteur: Optional[str] = None
    actif: bool = True
    sap_code: Optional[str] = None
    sf_id: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[str] = None
    type_poste: Optional[TypePoste] = None
    region_id: Optional[int] = None
    secteur: Optional[str] = None
    actif: Optional[bool] = None
    sap_code: Optional[str] = None
    sf_id: Optional[str] = None


class EmployeeRead(EmployeeBase):
    id: int
    region: Optional[RegionRead] = None
    model_config = {"from_attributes": True}
