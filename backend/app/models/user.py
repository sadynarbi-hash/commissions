from __future__ import annotations
import enum
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class UserRole(str, enum.Enum):
    ADMIN      = "ADMIN"
    DIRECTEUR  = "DIRECTEUR"
    ADJOINT    = "ADJOINT"
    LECTEUR    = "LECTEUR"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(300))
    nom: Mapped[str] = mapped_column(String(150))
    role: Mapped[str] = mapped_column(String(50), default=UserRole.LECTEUR)
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
