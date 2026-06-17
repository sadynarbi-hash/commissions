from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base, SessionLocal
from .routers import employees, objectives, bonuses, sync, dashboard, auth

# Import tous les modèles pour que Base les enregistre avant create_all
from .models import *  # noqa: F401, F403
from .models.employee import Region, TypeRegion

app = FastAPI(
    title="NMA Gestion des Primes",
    description="Système de calcul et suivi des primes commerciales 2026",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(objectives.router)
app.include_router(bonuses.router)
app.include_router(sync.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)
    _seed_regions()
    _seed_admin()


def _seed_regions():
    REGIONS = [
        ("DAKAR",   TypeRegion.NATIONALE),
        ("NORD",    TypeRegion.NATIONALE),
        ("CENTRE",  TypeRegion.NATIONALE),
        ("SUD",     TypeRegion.NATIONALE),
        ("EXPORT",  TypeRegion.EXPORT),
    ]
    db = SessionLocal()
    try:
        for nom, type_region in REGIONS:
            if not db.query(Region).filter(Region.nom == nom).first():
                db.add(Region(nom=nom, type=type_region))
        db.commit()
    finally:
        db.close()


def _seed_admin():
    from .models.user import User
    from .routers.auth import hash_password
    db = SessionLocal()
    try:
        if not db.query(User).first():
            db.add(User(
                email="admin@nma.sn",
                hashed_password=hash_password("nma2026"),
                nom="Administrateur NMA",
                role="ADMIN",
            ))
            db.commit()
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "NMA Primes API — v1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
