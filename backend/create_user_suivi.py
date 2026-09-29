"""
Crée le compte penda.diallo@nmasanders.com avec accès restreint à Suivi Compte.
Usage : python create_user_suivi.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.routers.auth import hash_password

EMAIL    = "penda.diallo@nmasanders.com"
PASSWORD = "NMA2026!"   # mot de passe initial à changer

db = SessionLocal()
try:
    existing = db.query(User).filter(User.email == EMAIL).first()
    if existing:
        print(f"L'utilisateur {EMAIL} existe déjà (id={existing.id}, role={existing.role})")
    else:
        user = User(
            email=EMAIL,
            hashed_password=hash_password(PASSWORD),
            nom="Penda Diallo",
            role=UserRole.SUIVI_ONLY,
            actif=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Compte créé : {user.email} (id={user.id}, role={user.role})")
        print(f"Mot de passe initial : {PASSWORD}")
finally:
    db.close()
