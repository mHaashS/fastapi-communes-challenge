from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from .database import create_tables, get_db
from .crud import get_commune_by_name, get_communes_by_departement, create_or_update_commune, get_communes_by_code_postal, supprimer_commune, get_communes_proches
from .schemas import CommuneBase, CommuneResponse, CommuneAvecDistance

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API Communes"}

@app.get("/health")
async def health():
    return {"message": "Service fonctionnel"}

@app.get("/communes/{nom}", response_model=CommuneResponse)
async def get_commune(nom: str, db: Session = Depends(get_db)):
    commune = get_commune_by_name(db, nom)
    if not commune:
        raise HTTPException(status_code=404, detail="Commune non trouvée")
    return commune

@app.get("/communes/departement/{departement}", response_model=List[CommuneResponse])
async def get_communes(departement: str, db: Session = Depends(get_db)):
    communes = get_communes_by_departement(db, departement)
    if not communes:
        raise HTTPException(status_code=404, detail="Aucune commune trouvée pour ce département")
    return communes

@app.get("/communes/code_postal/{code_postal}", response_model=List[CommuneResponse])
async def get_communes(code_postal: str, db: Session = Depends(get_db)):
    communes = get_communes_by_code_postal(db, code_postal)
    if not communes:
        raise HTTPException(status_code=404, detail="Aucune commune trouvée pour ce code postal")
    return communes

@app.post("/communes")
async def create_update_commune(commune: CommuneBase, db: Session = Depends(get_db)):
    try:
        return create_or_update_commune(db, commune)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création/mise à jour: {str(e)}")

@app.delete("/communes/{nom}")
async def delete_commune(nom: str, db: Session = Depends(get_db)):
    try:
        commune = supprimer_commune(db, nom)
        if not commune:
            raise HTTPException(status_code=404, detail="Commune non trouvée")
        return {"message": "Commune supprimée avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

@app.get("/communes/{nom}/proches", response_model=List[CommuneAvecDistance])
async def get_communes_proches_endpoint(
    nom: str, 
    nombre: int = Query(5, ge=1, le=50, description="Nombre de communes proches à retourner"),
    db: Session = Depends(get_db)
):
    try:
        communes_avec_distance = get_communes_proches(db, nom, nombre)
        return [
            CommuneAvecDistance(commune=commune, distance_km=distance)
            for commune, distance in communes_avec_distance
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche: {str(e)}")