from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, List

import jwt
import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

_bearer = HTTPBearer()

_ALGORITHM = "HS256"
_TOKEN_HOURS = 24


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=_TOKEN_HOURS),
    }
    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm=_ALGORITHM)


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "nom": user.nom,
        "role": user.role,
        "actif": user.actif,
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(
            credentials.credentials, settings.APP_SECRET_KEY, algorithms=[_ALGORITHM]
        )
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")

    user = db.query(User).filter(User.id == user_id, User.actif == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")
    return user


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    return current_user


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.email == body.email.strip().lower(),
        User.actif == True,
    ).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )
    return {"access_token": _create_token(user.id), "token_type": "bearer", "user": _user_dict(user)}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return _user_dict(current_user)


class CreateUserRequest(BaseModel):
    email: str
    password: str
    nom: str
    role: str = "LECTEUR"


class UpdateUserRequest(BaseModel):
    nom: Optional[str] = None
    role: Optional[str] = None
    actif: Optional[bool] = None


class ResetPasswordRequest(BaseModel):
    new_password: str


# ── Gestion des utilisateurs (ADMIN uniquement) ─────────────────────────────

@router.get("/users")
def list_users(
    _admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return [_user_dict(u) for u in db.query(User).order_by(User.nom).all()]


@router.post("/users", status_code=201)
def create_user(
    body: CreateUserRequest,
    _admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == body.email.strip().lower()).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Mot de passe trop court (6 caractères minimum)")
    user = User(
        email=body.email.strip().lower(),
        hashed_password=hash_password(body.password),
        nom=body.nom.strip(),
        role=body.role,
        actif=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_dict(user)


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    body: UpdateUserRequest,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if user.id == admin.id and body.role and body.role != "ADMIN":
        raise HTTPException(status_code=400, detail="Impossible de retirer votre propre rôle ADMIN")
    if body.nom is not None:
        user.nom = body.nom.strip()
    if body.role is not None:
        user.role = body.role
    if body.actif is not None:
        user.actif = body.actif
    db.commit()
    return _user_dict(user)


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    body: ResetPasswordRequest,
    _admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Mot de passe trop court (6 caractères minimum)")
    user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"detail": "Mot de passe réinitialisé"}


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Le nouveau mot de passe doit faire au moins 6 caractères")
    current_user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"detail": "Mot de passe modifié"}
