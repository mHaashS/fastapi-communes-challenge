from sqlalchemy.orm import Session
from typing import List, Optional
from .models import Commune
from .schemas import CommuneBase

def get_commune_by_name(db: Session, nom: str) -> Optional[Commune]:
    """
    Récupère une commune par son nom
    
    Args:
        db: Session de base de données
        nom: Nom de la commune
        
    Returns:
        Commune ou None si non trouvée
    """
    return db.query(Commune).filter(Commune.nom_complet == nom.upper()).first()

def get_communes_by_departement(db: Session, departement: str) -> List[Commune]:
    """
    Récupère toutes les communes d'un département
    
    Args:
        db: Session de base de données
        departement: Code du département
        
    Returns:
        Liste de communes
    """
    return db.query(Commune).filter(Commune.departement == departement).all()

def get_communes_by_code_postal(db: Session, code_postal: str) -> List[Commune]:
    """
    Récupère toutes les communes d'un code postal
    
    Args:
        db: Session de base de données
        code_postal: Code postal
        
    Returns:
        Liste de communes
    """
    return db.query(Commune).filter(Commune.code_postal == code_postal).all()

def create_or_update_commune(db: Session, commune: CommuneBase) -> Commune:
    """
    Crée une nouvelle commune ou met à jour une commune existante
    
    Args:
        db: Session de base de données
        commune: Données de la commune à créer
        
    Returns:
        Commune créée
    """
    # Chercher si une commune avec le même nom existe déjà
    existing_commune = db.query(Commune).filter(
        Commune.nom_complet == commune.nom_complet.upper()
    ).first()
    
    if existing_commune:
        # Mettre à jour la commune existante
        existing_commune.code_postal = commune.code_postal
        existing_commune.departement = commune.departement
        db.commit()
        db.refresh(existing_commune)
        return existing_commune
    else:
        # Créer une nouvelle commune
        commune.nom_complet = commune.nom_complet.upper()
        db_commune = Commune(**commune.model_dump())
        db.add(db_commune)
        db.commit()
        db.refresh(db_commune)
        return db_commune