import enum
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum as SAEnum, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class TypeVisite(str, enum.Enum):
    CLIENT = "CLIENT"
    FERME = "FERME"
    PROSPECTION = "PROSPECTION"


class VisitData(Base):
    __tablename__ = "visits_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    sf_id: Mapped[str] = mapped_column(String(50), unique=True)
    employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    client_code: Mapped[Optional[str]] = mapped_column(String(50))
    client_nom: Mapped[Optional[str]] = mapped_column(String(200))
    type_visite: Mapped[TypeVisite] = mapped_column(SAEnum(TypeVisite))
    date_visite: Mapped[datetime] = mapped_column(DateTime)
    commande_saisie: Mapped[bool] = mapped_column(Boolean, default=False)
    visite_saisie_crm: Mapped[bool] = mapped_column(Boolean, default=True)
    kpis_json: Mapped[Optional[dict]] = mapped_column(JSON)
    periode: Mapped[str] = mapped_column(String(7))
    sync_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    employee: Mapped[Optional["Employee"]] = relationship(back_populates="visits")


class ManualCriteria(Base):
    __tablename__ = "manual_criteria"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    periode: Mapped[str] = mapped_column(String(7))
    critere_code: Mapped[str] = mapped_column(String(50))
    valeur: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500))
    saisi_par: Mapped[Optional[str]] = mapped_column(String(100))
    saisi_le: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
