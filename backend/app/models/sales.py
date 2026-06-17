import enum
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from .objective import Gamme


class StatutRecouvrement(str, enum.Enum):
    EN_ATTENTE = "EN_ATTENTE"
    PARTIEL = "PARTIEL"
    RECOUVRE = "RECOUVRE"


class SaleData(Base):
    __tablename__ = "sales_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(String(50), unique=True)
    employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    client_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clients.id"))
    client_code: Mapped[Optional[str]] = mapped_column(String(50))
    client_nom: Mapped[Optional[str]] = mapped_column(String(200))
    gamme: Mapped[Gamme] = mapped_column(SAEnum(Gamme, native_enum=False))
    volume: Mapped[float] = mapped_column(Numeric(15, 3))
    montant_ht: Mapped[float] = mapped_column(Numeric(15, 2))
    montant_recouvre: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    statut_recouvrement: Mapped[StatutRecouvrement] = mapped_column(
        SAEnum(StatutRecouvrement), default=StatutRecouvrement.EN_ATTENTE
    )
    date_facture: Mapped[datetime] = mapped_column(DateTime)
    periode: Mapped[str] = mapped_column(String(7))
    annee_n1: Mapped[bool] = mapped_column(default=False)
    sync_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    employee: Mapped[Optional["Employee"]] = relationship(back_populates="sales")


class SyncSourceType(str, enum.Enum):
    SAP = "SAP"
    SALESFORCE = "SALESFORCE"


class SyncStatut(str, enum.Enum):
    EN_COURS = "EN_COURS"
    SUCCES = "SUCCES"
    ERREUR = "ERREUR"


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[SyncSourceType] = mapped_column(SAEnum(SyncSourceType))
    periode: Mapped[Optional[str]] = mapped_column(String(7))
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    statut: Mapped[SyncStatut] = mapped_column(
        SAEnum(SyncStatut), default=SyncStatut.EN_COURS
    )
    nb_records: Mapped[int] = mapped_column(default=0)
    message: Mapped[Optional[str]] = mapped_column(String(1000))
