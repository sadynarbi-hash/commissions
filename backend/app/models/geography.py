from __future__ import annotations
from typing import Optional, List
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Zone(Base):
    """Miroir de @ZONESLIGNES SAP.
    Contient superviseur (SV), responsable régional (RCR) et docteur (RESP_TECH).
    """
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)   # Z1, Z2, Z3, Z4, Z5, Z6
    nom: Mapped[str] = mapped_column(String(50))                  # DAKAR, CENTRE, NORD, SUD

    superviseur_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    responsable_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    docteur_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))

    secteurs_geo: Mapped[List["SecteurGeo"]] = relationship(back_populates="zone")


class SecteurGeo(Base):
    """Miroir de @SECTEURSLIGNE SAP — secteur géographique sans gamme ni commercial.
    Ex : Z1S1 = Plateau (Zone Z1).
    """
    __tablename__ = "secteurs_geo"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)  # Z1S1, Z2S1...
    nom: Mapped[str] = mapped_column(String(100))                     # Plateau, Thies...
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"))

    zone: Mapped["Zone"] = relationship(back_populates="secteurs_geo")
    secteurs: Mapped[List["Secteur"]] = relationship(back_populates="secteur_geo")


class Secteur(Base):
    """Miroir de @COMSECTEURLIGNE SAP — secteur commercial avec gamme et commercial assigné.
    code = U_CODE SAP = valeur de OCRD.U_Secteur sur les clients.
    Ex : Z1S1BV = Plateau / BETAIL-VOL → MAMADOU DIAGNE.
    Changer de commercial = UPDATE secteurs SET employee_id = X WHERE code = 'Z1S1BV'.
    """
    __tablename__ = "secteurs"

    code: Mapped[str] = mapped_column(String(15), primary_key=True)  # Z1S1BV, Z1S1PA...
    gamme: Mapped[Optional[str]] = mapped_column(String(20))          # BETAIL/VOL, PATE...
    secteur_geo_code: Mapped[str] = mapped_column(ForeignKey("secteurs_geo.code"))

    # Commercial assigné — seul champ à changer lors d'une mutation
    employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    # Responsable technique (RESP_TECH_BV ou RESP_TECH_FP)
    docteur_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))

    secteur_geo: Mapped["SecteurGeo"] = relationship(back_populates="secteurs")
