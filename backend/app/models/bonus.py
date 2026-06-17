import enum
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Numeric, Boolean, DateTime, ForeignKey, Enum as SAEnum, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class StatutBonus(str, enum.Enum):
    BROUILLON = "BROUILLON"
    CALCULE = "CALCULE"
    EN_VALIDATION = "EN_VALIDATION"
    VALIDE = "VALIDE"
    PAYE = "PAYE"


class BonusPeriod(Base):
    __tablename__ = "bonus_periods"

    id: Mapped[int] = mapped_column(primary_key=True)
    periode: Mapped[str] = mapped_column(String(7), unique=True)
    statut: Mapped[StatutBonus] = mapped_column(
        SAEnum(StatutBonus), default=StatutBonus.BROUILLON
    )
    date_calcul: Mapped[Optional[datetime]] = mapped_column(DateTime)
    valide_par: Mapped[Optional[str]] = mapped_column(String(100))
    date_validation: Mapped[Optional[datetime]] = mapped_column(DateTime)

    bonuses: Mapped[List["Bonus"]] = relationship(back_populates="period")


class Bonus(Base):
    __tablename__ = "bonuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("bonus_periods.id"))

    taux_atteinte_global: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    taux_atteinte_pates: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    taux_atteinte_autres: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))

    volume_realise: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    volume_objectif: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    nb_visites: Mapped[int] = mapped_column(default=0)

    prime_suivi_fixe: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    prime_quantitative: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    prime_qualitative: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    commission_nouvelles_affaires: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    qualitative_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    detail_json: Mapped[Optional[dict]] = mapped_column(JSON)
    statut: Mapped[StatutBonus] = mapped_column(
        SAEnum(StatutBonus), default=StatutBonus.CALCULE
    )
    observations: Mapped[Optional[str]] = mapped_column(String(500))
    calcule_le: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    employee: Mapped["Employee"] = relationship(back_populates="bonuses")
    period: Mapped["BonusPeriod"] = relationship(back_populates="bonuses")
    qual_details: Mapped[List["BonusQualDetail"]] = relationship(back_populates="bonus")


class BonusQualDetail(Base):
    __tablename__ = "bonus_qual_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    bonus_id: Mapped[int] = mapped_column(ForeignKey("bonuses.id"))
    critere_code: Mapped[str] = mapped_column(String(50))
    critere_libelle: Mapped[str] = mapped_column(String(200))
    valeur_atteinte: Mapped[Optional[str]] = mapped_column(String(100))
    seuil_requis: Mapped[Optional[str]] = mapped_column(String(100))
    montant_max: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    montant_accorde: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    eligible: Mapped[bool] = mapped_column(Boolean, default=False)

    bonus: Mapped["Bonus"] = relationship(back_populates="qual_details")
