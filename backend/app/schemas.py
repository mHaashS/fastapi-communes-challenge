from pydantic import BaseModel, Field

class CommuneBase(BaseModel):
    """Schéma de base pour une commune"""
    code_postal: str = Field(..., min_length=5, max_length=5)
    nom_complet: str = Field(..., min_length=1, max_length=100)
    departement: str = Field(..., min_length=2, max_length=3)

class CommuneResponse(CommuneBase):
    """Schéma de réponse pour une commune"""
    id: int = Field(..., description="Identifiant unique de la commune")
    
    class Config:
        from_attributes = True