from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Tuple
import requests
import math
import json
import os
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

    commune =  db.query(Commune).filter(Commune.nom_complet == nom.upper()).first()

    if commune:
        print(f"Commune trouvée: {commune.nom_complet}, lat: {commune.latitude}, lon: {commune.longitude}")
        if commune.latitude is None or commune.longitude is None:
            print(f"Récupération des coordonnées pour: {commune.nom_complet}, {commune.code_postal}")
            coordonnees = coordonnees_commune(nom_commune=commune.nom_complet, code_postal=commune.code_postal)
            print(f"Coordonnées récupérées: {coordonnees}")
            if coordonnees:
                commune.latitude = coordonnees['latitude']
                commune.longitude = coordonnees['longitude']
                db.commit()
                db.refresh(commune)
                print(f"Coordonnées sauvegardées: lat={commune.latitude}, lon={commune.longitude}")
            else:
                print("Aucune coordonnée récupérée")
        else:
            print("Coordonnées déjà en base de données")
    else:
        print(f"Commune non trouvée: {nom}")
    
    return commune



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

    communes =  db.query(Commune).filter(Commune.code_postal == code_postal).all()

    for commune in communes:
        if commune.latitude is None or commune.longitude is None:
            coordonnees = coordonnees_commune(nom_commune=commune.nom_complet, code_postal=commune.code_postal)
            if coordonnees:
                commune.latitude = coordonnees['latitude']
                commune.longitude = coordonnees['longitude']
    db.commit()

    for commune in communes:
        db.refresh(commune)

    return communes


def create_or_update_commune(db: Session, commune: CommuneBase) -> Commune:
    """
    Crée une nouvelle commune ou met à jour une commune existante
    
    Args:
        db: Session de base de données
        commune: Données de la commune à créer
        
    Returns:
        Commune créée
    """

    # Récupérer les coordonnées GPS
    coordonnees = coordonnees_commune(commune.nom_complet, commune.code_postal)

    # Chercher si une commune avec le même nom existe déjà
    existing_commune = db.query(Commune).filter(
        Commune.nom_complet == commune.nom_complet.upper()
    ).first()
    
    if existing_commune:
        # Mettre à jour la commune existante
        existing_commune.code_postal = commune.code_postal
        existing_commune.departement = commune.departement

        if coordonnees is not None:
            existing_commune.latitude = coordonnees['latitude']
            existing_commune.longitude = coordonnees['longitude']
            print(f"Latitude: {existing_commune.latitude}, Longitude: {existing_commune.longitude}")

        db.commit()
        db.refresh(existing_commune)
        return existing_commune
    else:
        # Créer une nouvelle commune
        commune.nom_complet = commune.nom_complet.upper()
        db_commune = Commune(**commune.model_dump())

        if coordonnees is not None:
            db_commune.latitude = coordonnees['latitude']
            db_commune.longitude = coordonnees['longitude']
            print(f"Latitude: {db_commune.latitude}, Longitude: {db_commune.longitude}")

        db.add(db_commune)
        db.commit()
        db.refresh(db_commune)
        return db_commune


def coordonnees_commune(nom_commune: Optional[str] = None, code_postal: Optional[str] = None) -> Optional[Dict[str, float]]:
    """
    Récupère les coordonnées GPS via Nominatim
    
    Args:
        nom_commune: Nom de la commune
        code_postal: Code postal de la commune
        
    Returns:
        Dict[str, float] ou None si erreur
    """

    if nom_commune is None and code_postal is None:
        return None

    try:
        #url = "https://nominatim.openstreetmap.org/search"
        url = "http://nominatim:8080/search"

        query_parts = []
        if nom_commune:
            query_parts.append(nom_commune)
        if code_postal:
            query_parts.append(code_postal)
        query_parts.append("France")

        params = {
            'q': ", ".join(query_parts),
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
            'countrycodes': 'fr'
        }
        
        headers = {
            'User-Agent': 'FastAPI-Commune-App/1.0'
        }
        
        response = requests.get(url, params=params, timeout=10, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                return {
                    'latitude': float(data[0]['lat']),
                    'longitude': float(data[0]['lon'])
                }
    except Exception as e:
        print(f"Erreur de géocodage: {e}")
    
    return None

def supprimer_commune(db: Session, nom_commune: str) -> Optional[Commune]:
    """
    Supprime une commune de la base de données
    
    Args:
        db: Session de base de données
        commune: Commune à supprimer
    """
    commune = db.query(Commune).filter(Commune.nom_complet == nom_commune.upper()).first()

    if not commune:
        return None

    db.delete(commune)
    db.commit()
    return commune


"""
Fonction pour récuperer les communes les plus proches
Récupère les communes du département et des départements voisins
Les départements voisins seraient stockés dans un dictionnaire du type:
{  
    "69": ["69","01","38","42","71"],
    "01": ["01","69", "71", "38", "74", "73"],
    etc...
}
Récupere les voisins avec 
communes_meme_departement = db.query(Commune).filter(
    Commune.id != commune_ref.id,
    Commune.departement.in_(voisins)   # <- utiliser in_() ici
).all()

calcul des coordonnées pour chaque commune du département et des départements voisins
En france en moyenne 4 départements voisins par département et 300 communes par département
Temps moyen d'une requete nominatim pour une commune : 100ms
100ms * 300 communes * 4 départements voisins = 120000ms = 120s = 2 minutes
ajout en bdd les coordonées de chaque commune calculées

Calcul de la distance avec toutes les autres communes avec la formule de haversine
R = 6371 km
d = 2 * R * arcsin(sqrt(sin²((lat2-lat1)/2) + cos(lat1) * cos(lat2) * sin²((lon2-lon1)/2)))

Une fois que j'ai les distances de toutes les communes du département et des départements voisins
je trie les communes par distance et je retourne les n communes les plus proches (n = nombre choisi par l'utilisateur)
"""

def calculer_distance_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcule la distance entre deux points GPS en utilisant la formule de Haversine
    Args:
        lat1: Latitude du premier point
        lon1: Longitude du premier point
        lat2: Latitude du deuxième point
        lon2: Longitude du deuxième point
    Returns:
        Distance en kilomètres
    """
    R = 6371.0  # Rayon de la Terre en km
    
    # Conversion en radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Différences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Formule de Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def charger_departements_voisins() -> Dict[str, List[str]]:
    """
    Charge le fichier JSON des départements voisins
    Args:
        None
    Returns:
        Dict[str, List[str]]
    """
    # Chemin vers le fichier JSON (à partir du répertoire racine du projet)
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "departements_voisins.json")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Fichier {json_path} non trouvé")
        return {}
    except json.JSONDecodeError as e:
        print(f"Erreur de lecture du JSON: {e}")
        return {}

def get_communes_proches(db: Session, nom_commune: str, nombre: int = 5) -> List[Tuple[Commune, float]]:
    """
    Récupère les x communes les plus proches d'une commune donnée
    Récupère les communes du département et des départements voisins
    Args:
        db: Session de base de données
        nom_commune: Nom de la commune
        nombre: Nombre de communes à retourner
    Returns:
        List[Tuple[Commune, float]]
    """
    # Récupérer la commune de référence
    commune_ref = get_commune_by_name(db, nom_commune)
    if not commune_ref:
        raise ValueError(f"Commune '{nom_commune}' non trouvée")
    
    if commune_ref.latitude is None or commune_ref.longitude is None:
        raise ValueError(f"Coordonnées GPS manquantes pour la commune '{nom_commune}'")
    
    # Charger les départements voisins
    departements_voisins = charger_departements_voisins()
    departements_a_chercher = departements_voisins.get(commune_ref.departement, [commune_ref.departement])
    
    print(f"Recherche dans les départements: {departements_a_chercher}")
    
    # Récupérer toutes les communes des départements voisins
    communes_voisines = db.query(Commune).filter(
        Commune.id != commune_ref.id,
        Commune.departement.in_(departements_a_chercher)
    ).all()
    
    communes_avec_distance = []
    
    # Calculer les coordonnées pour chaque commune et la distance
    for i, commune in enumerate(communes_voisines):
        
        # Récupérer les coordonnées si elles manquent
        if commune.latitude is None or commune.longitude is None:
            coordonnees = coordonnees_commune(
                nom_commune=commune.nom_complet,
                code_postal=commune.code_postal
            )
            if coordonnees:
                commune.latitude = coordonnees['latitude']
                commune.longitude = coordonnees['longitude']
                db.commit()
                db.refresh(commune)
                print(f"Coordonnées récupérées: lat={coordonnees['latitude']}, lon={coordonnees['longitude']}")
            else:
                print(f"Impossible de récupérer les coordonnées")
                continue  # Passer à la commune suivante
        
        # Calculer la distance avec la commune de référence
        if commune.latitude is not None and commune.longitude is not None:
            distance = calculer_distance_haversine(
                commune_ref.latitude, commune_ref.longitude,
                commune.latitude, commune.longitude
            )
            communes_avec_distance.append((commune, distance))
    
    # Trier par distance croissante et retourner les n communes les plus proches
    communes_avec_distance.sort(key=lambda x: x[1])
    
    return communes_avec_distance[:nombre]