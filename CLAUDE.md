# NMA Gestion des Primes Commerciales 2026

## Contexte
Application de gestion des primes commerciales pour **Nouvelle Minoterie Africaine (NMA)**.
Calcule les primes quantitatives et qualitatives selon le document "SYSTEME DE PRIMES 2026 V11".

## Stack technique
- **Backend** : Python 3.9 + FastAPI + SQLAlchemy 2.0
- **Base locale** : PostgreSQL (`nma_primes` — user `damesady`)
- **Frontend** : React + TypeScript + Ant Design (charte couleurs NMA)
- **SAP B1** : pymssql (connexion directe SQL Server — pas pyodbc, TLS incompatible)
- **Salesforce** : simple-salesforce (visites terrain)

## Lancer l'application

```bash
# Terminal 1 — Backend
cd /Users/damesady/developpement/Commerciaux/backend
source venv/bin/activate
uvicorn app.main:app --reload
# → http://localhost:8000  (docs: http://localhost:8000/docs)

# Terminal 2 — Frontend
cd /Users/damesady/developpement/Commerciaux/frontend
npm run dev
# → http://localhost:5173
```

## Base de données

```bash
# Recréer la base (si besoin de repartir à zéro)
dropdb nma_primes && createdb nma_primes

# Peupler dans l'ordre
python -m app.seed              # régions + 31 employés
python -m app.seed_sap_codes    # codes SAP (SlpCode) par commercial
python -m app.seed_objectives   # 398 objectifs 2026 (CENTRE/NORD/SUD/DAKAR)
```

## Connexion SAP B1

- **Credentials** : voir `backend/.env` (ne pas commiter)
- **Driver** : pymssql (ODBC Driver 18 for SQL Server refusé — TLS 1.2 incompatible avec ce SQL Server)
- **Tables utilisées** : DLN1 + ODLN (bons de livraison), OSLP (vendeurs), OUSR (utilisateurs)
- **Filtre articles** : uniquement codes commençant par `PF` (produits finis)

### Détection automatique des gammes
| Préfixe article | Gamme |
|-----------------|-------|
| `PFBE`          | BETAIL |
| `PFFA`          | FARINE |
| `PFPA`          | PATES |
| `PFVO`          | VOLAILLE |
| `PFNE`          | Ignoré (négoce) |

### Test connexion SAP
```bash
python3 -c "
from app.config import settings
from app.services.sap_connector import get_sap_connector
c = get_sap_connector(settings)
print('OK' if c and c.test_connection() else 'ECHEC')
"
```

### Synchronisation manuelle
```bash
python3 -c "
from app.database import SessionLocal
from app.config import settings
from app.services.sap_connector import get_sap_connector
from app.services.sync_sap import sync_sales
from datetime import date
db = SessionLocal()
c = get_sap_connector(settings)
result = sync_sales(db, c, date(2026, 1, 1), date(2026, 1, 31))
print(result)
db.close()
"
```

## Zones et équipe

| Zone   | RCR              | SV             | SAP code RCR |
|--------|------------------|----------------|--------------|
| DAKAR  | AICHA FALL       | MOUSSA NIANG   | 61           |
| NORD   | FATMA AMAR       | AMBROISE MENDY | 41           |
| CENTRE | PAPE FATA FAYE   | ISMAILA NDIAYE | 60           |
| SUD    | SOULEYMANE COLY  | (idem RCR)     | 7            |

### Codes SAP commerciaux clés
| Commercial           | SAP code | Zone   |
|----------------------|----------|--------|
| FATMA DIAGNE         | 53       | DAKAR  |
| MAMADOU DIAGNE       | 52       | DAKAR  |
| EL H MANDOUMBE MBAYE | 56       | DAKAR  |
| IBRAHIMA FALL        | 54       | DAKAR  |
| MOUSSA KEBE          | 44       | DAKAR  |
| ANTA KONATE          | 26       | DAKAR  |
| DIARRA DIOP          | 25       | DAKAR  |
| ABDOU NIANE          | 66       | DAKAR  |
| AMADOU KATY NDIAYE   | 51       | NORD   |
| MOUHAMED DIAGNE      | 34       | NORD   |
| PAPE SAMBA SOW       | 29       | NORD   |
| SOGUI DIOUF KA       | 49       | NORD   |
| CHEIKH FILY CISSOKHO | 6        | CENTRE |
| MODOU NGOM           | 62       | CENTRE |
| ALASSANE WADE        | 32       | CENTRE |
| PAPE MALICK GNINGUE  | 31       | CENTRE |
| KHADIME WADE         | 42       | CENTRE |
| MEDOUNE YALLY        | 55       | SUD    |
| FATOUMATA KANTE      | 15       | SUD    |
| SERIGNE AMADOU TOURE | 36       | SUD    |
| ISMA BA              | 23       | SUD    |
| BABACAR NDOYE (DCMT) | 4        | —      |

> **Note SAP** : Certains noms différent entre SAP et notre base :
> - SAP "BAMBA WADE" = ALASSANE WADE (prénom complet : Cheikh Ahmadou Bamba Wade)
> - SAP "MANOUMBE MBAYE" = EL H MANDOUMBE MBAYE
> - SAP "MAME DIARRA DIOP" = DIARRA DIOP
> - SAP "PAPA SAMBA SOW" = PAPE SAMBA SOW
> - SAP "HAICHA TALL" = AICHA FALL (code 61)
> - SAP "NDEYE KHADY DIAGNE" = NDEYE KHADY DIOP (code 65)
> - SAP "CISSOKO FILY CHEIKH" = CHEIKH FILY CISSOKHO (code 6)

## Structure des objectifs 2026

- **CENTRE** : données de Mars à Décembre uniquement
- **SUD** : données de Mars à Décembre uniquement
- **NORD** : données de Janvier à Décembre
- **DAKAR** : données de Janvier à Décembre
- Unité : **tonnes**
- Source : fichiers Excel centre.pdf, nord.pdf, Sud.pdf, Dakar.pdf

## Système de primes (résumé)

### Commerciaux
- Prime fixe : 100 000 FCFA
- Prime quantitative : 90%→250k | 100%→350k | 115%→500k
- Prime qualitative : 150 000 FCFA max (si ≥90% objectifs)

### RCR
- Prime quantitative : 90%→250k | 100%→350k | 115%→500k
- Prime qualitative : 200 000 FCFA max (si ≥90% objectifs)

### SV
- Prime quantitative Pâtes + Autres gammes séparées
- Prime qualitative : 150 000 FCFA max

### ATC Bétail & Volaille
- Prime quantitative : 90%→150k | 100%→250k | 115%→350k
- Prime qualitative : 200 000 FCFA max

## Charte couleurs NMA
- Vert foncé : `#1B5E20`
- Vert sidebar : `#0D3B12`
- Or/Blé : `#F9A825`
- Orange : `#E65100`
- Fond général : `#f4f6f0`

## Fichiers importants
```
backend/
  app/
    seed.py              # employés + régions
    seed_sap_codes.py    # codes SAP
    seed_objectives.py   # objectifs 2026
    services/
      sap_connector.py   # connecteur pymssql + détection gamme
      sync_sap.py        # service de sync BL → sales_data
    models/
      objective.py       # enum Gamme : BETAIL/VOLAILLE/FARINE/PATES
frontend/
  src/
    components/AppLayout/  # sidebar + header NMA
    pages/
      Objectives/          # tableau avec totaux par gamme + filtre zone
      Employees/           # grid avec avatars colorés par rôle
```

## À faire
- [ ] Connecter Salesforce (visites terrain)
- [ ] Implémenter le moteur de calcul des primes (bonus_engine.py)
- [ ] Page tableau de bord avec KPIs
- [ ] Workflow validation des primes (brouillon → validé → payé)
- [ ] Export Excel/PDF pour la paie
- [ ] Renseigner les codes SAP manquants (MARIAMA BA, BABACAR NDOYE DV)
