# NMA — Gestion des Commissions Commerciales

## Architecture

```
backend/   FastAPI + SQLAlchemy + PostgreSQL
frontend/  React + Ant Design + Vite
```

---

## Déploiement serveur (Docker — recommandé)

### 1. Prérequis sur le serveur Linux

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y git docker.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER   # puis se reconnecter
```

### 2. Récupérer le code

```bash
git clone <url-du-repo> /opt/nma-commissions
cd /opt/nma-commissions
```

### 3. Configurer les variables d'environnement

```bash
# Fichier racine pour docker-compose
cp .env.example .env
nano .env          # renseigner DB_PASSWORD

# Fichier backend production
cp backend/.env.production backend/.env.production
nano backend/.env.production   # vérifier SAP_SERVER, SAP_PASSWORD, APP_SECRET_KEY
```

> ⚠️ **Important** : changer `APP_SECRET_KEY` pour une chaîne aléatoire longue :
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```

### 4. Lancer l'application

```bash
docker compose up -d --build
```

L'application est disponible sur **http://IP_DU_SERVEUR**

### 5. Vérifier que tout tourne

```bash
docker compose ps          # tous les services doivent être "Up"
docker compose logs -f     # voir les logs en direct
```

---

## Mise à jour (après modifications)

```bash
cd /opt/nma-commissions
git pull
docker compose up -d --build
```

Les données PostgreSQL sont préservées dans un volume Docker (`postgres_data`).

---

## Sauvegarde de la base de données

```bash
# Dump
docker exec nma_db pg_dump -U nma nma_primes > backup_$(date +%Y%m%d).sql

# Restaurer
docker exec -i nma_db psql -U nma nma_primes < backup_20260101.sql
```

---

## Développement local

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # configurer DATABASE_URL, SAP, etc.
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Workflow mensuel

1. **Synchroniser SAP B1** → page Synchronisation, sélectionner le mois
2. **Saisir critères qualitatifs** → page Critères qualitatifs
3. **Calculer les commissions** → page Commissions, bouton "Calculer commissions"
4. **Valider** → bouton Valider (saisir votre nom)
5. **Exporter Excel** → bouton Export → transmission à la paie

---

## Gestion des comptes utilisateurs

Page **Paramètres → Utilisateurs** (rôle ADMIN requis)

Rôles disponibles : `ADMIN`, `DIRECTEUR`, `ADJOINT`, `LECTEUR`
