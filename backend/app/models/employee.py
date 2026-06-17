import enum
from typing import Optional, List
from sqlalchemy import String, Boolean, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class TypePoste(str, enum.Enum):
    RCR = "RCR"
    SV = "SV"
    COMMERCIAL = "COMMERCIAL"
    ATC_BV = "ATC_BV"
    ATC_FARINE = "ATC_FARINE"
    RCE = "RCE"
    RESP_TECH_FP = "RESP_TECH_FP"
    RESP_TECH_BV = "RESP_TECH_BV"
    DV = "DV"
    DCMT = "DCMT"

    @property
    def label(self) -> str:
        labels = {
            "RCR": "Resp. Commercial Régional",
            "SV": "Superviseur des Ventes",
            "COMMERCIAL": "Commercial",
            "ATC_BV": "Agent TC Bétail & Volaille",
            "ATC_FARINE": "Agent TC Farine",
            "RCE": "Resp. Commercial Export",
            "RESP_TECH_FP": "Resp. Technique Farine & Pâtes",
            "RESP_TECH_BV": "Resp. Technique Bétail & Volaille",
            "DV": "Directeur des Ventes",
            "DCMT": "Directeur Commercial Marketing Tech.",
        }
        return labels.get(self.value, self.value)


class TypeRegion(str, enum.Enum):
    NATIONALE = "NATIONALE"
    EXPORT = "EXPORT"


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), unique=True)
    type: Mapped[TypeRegion] = mapped_column(
        SAEnum(TypeRegion), default=TypeRegion.NATIONALE
    )

    employees: Mapped[List["Employee"]] = relationship(back_populates="region")


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    prenom: Mapped[str] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    type_poste: Mapped[TypePoste] = mapped_column(SAEnum(TypePoste))
    region_id: Mapped[Optional[int]] = mapped_column(ForeignKey("regions.id"))
    zone_id: Mapped[Optional[int]] = mapped_column(ForeignKey("zones.id"))
    secteur: Mapped[Optional[str]] = mapped_column(String(100))
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    sap_code: Mapped[Optional[str]] = mapped_column(String(50))
    sf_id: Mapped[Optional[str]] = mapped_column(String(50))

    region: Mapped[Optional["Region"]] = relationship(back_populates="employees")
    objectives: Mapped[List["Objective"]] = relationship(back_populates="employee")
    bonuses: Mapped[List["Bonus"]] = relationship(back_populates="employee")
    sales: Mapped[List["SaleData"]] = relationship(back_populates="employee")
    visits: Mapped[List["VisitData"]] = relationship(back_populates="employee")
    portfolio: Mapped[List["ClientPortfolio"]] = relationship(back_populates="employee")
