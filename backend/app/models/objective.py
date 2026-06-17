import enum
from typing import Optional, List
from datetime import date
from sqlalchemy import String, Numeric, Integer, Date, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Gamme(str, enum.Enum):
    BETAIL = "BETAIL"
    VOLAILLE = "VOLAILLE"
    BVF = "BVF"          # agrégat BETAIL+VOLAILLE (utilisé pour calcul primes)
    PATES = "PATES"
    FARINE = "FARINE"
    NUTRITION_ANIMALE = "NUTRITION_ANIMALE"
    ALL = "ALL"
    AUTRES = "AUTRES"    # articles hors gammes PF (négoce, transport, divers)


class Objective(Base):
    __tablename__ = "objectives"
    __table_args__ = (
        UniqueConstraint("employee_id", "periode", "gamme", name="uq_obj_emp_periode_gamme"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    periode: Mapped[str] = mapped_column(String(7))
    gamme: Mapped[Gamme] = mapped_column(SAEnum(Gamme, native_enum=False))
    objectif_volume: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    objectif_ca: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))

    employee: Mapped["Employee"] = relationship(back_populates="objectives")


class SalesForecast(Base):
    __tablename__ = "sales_forecasts"
    __table_args__ = (
        UniqueConstraint("employee_id", "periode", "gamme", name="uq_forecast_emp_periode_gamme"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    periode: Mapped[str] = mapped_column(String(7))
    gamme: Mapped[Gamme] = mapped_column(SAEnum(Gamme, native_enum=False))
    volume_prevu: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    ca_prevu: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    code_sap: Mapped[str] = mapped_column(String(50), unique=True)
    nom: Mapped[str] = mapped_column(String(200))
    region_id: Mapped[Optional[int]] = mapped_column(ForeignKey("regions.id"))
    # U_Secteur depuis OCRD SAP — référence secteurs.code (ex: Z1S1BV)
    u_secteur: Mapped[Optional[str]] = mapped_column(String(15))
    gamme_principale: Mapped[Optional[Gamme]] = mapped_column(SAEnum(Gamme, native_enum=False))
    date_ouverture: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actif: Mapped[bool] = mapped_column(default=True)

    portfolio: Mapped[List["ClientPortfolio"]] = relationship(back_populates="client")


class ClientPortfolio(Base):
    __tablename__ = "client_portfolios"
    __table_args__ = (
        UniqueConstraint("employee_id", "client_id", "annee", name="uq_portfolio"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    annee: Mapped[int] = mapped_column(Integer)

    employee: Mapped["Employee"] = relationship(back_populates="portfolio")
    client: Mapped["Client"] = relationship(back_populates="portfolio")


class ClientMonthlySale(Base):
    """Volumes livrés par client par mois — alimenté depuis DLN1 au moment de la sync."""
    __tablename__ = "client_monthly_sales"
    __table_args__ = (
        UniqueConstraint("employee_id", "client_code", "periode", "annee_n1",
                         name="uq_client_monthly_sale"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    client_code: Mapped[str] = mapped_column(String(50))
    client_nom: Mapped[Optional[str]] = mapped_column(String(200))
    periode: Mapped[str] = mapped_column(String(7))
    volume: Mapped[float] = mapped_column(Numeric(15, 3), default=0)
    montant_ca: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    annee_n1: Mapped[bool] = mapped_column(default=False)
