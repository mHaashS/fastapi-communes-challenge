# ��️ FastAPI Communes Challenge

Une API REST pour rechercher et gérer les communes françaises avec géocodage automatique.

## 🚀 Démarrage rapide

### Prérequis
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git

### Installation

```bash
# 1. Cloner le projet
git clone https://github.com/mHaashS/fastapi-communes-challenge.git
cd fastapi-communes-challenge/

# Créer un fichier .env 
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/communes_db
POSTGRES_DB=communes_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# 2. Démarrer les services
docker-compose up --build
```

### Chargement des données

```bash
# Dans un nouveau terminal
docker-compose exec fastapi python backend/etl/pipeline.py
```

### Accès à l'API

- **API principale** : http://localhost:8000
- **Documentation interactive** : http://localhost:8000/docs
- **Health check** : http://localhost:8000/health

## �� Endpoints disponibles

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/` | Acceuil |
| `GET` | `/health` | Vérification de santé |
| `GET` | `/communes/{nom}` | Rechercher une commune par nom |
| `GET` | `/communes/departement/{departement}` | Communes par département |
| `GET` | `/communes/code_postal/{code_postal}` | Communes par code postal |
| `POST` | `/communes` | Créer/modifier une commune |
| `DELETE` | `/communes/{nom}` | Supprimer une commune |