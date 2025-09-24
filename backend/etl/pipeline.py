import pandas as pd
import sys
import os

# Ajouter le chemin vers le dossier app pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from database import SessionLocal, engine
from models import Commune, Base

# Créer les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

#Ce que j’aurais fait si l’URL avait fonctionné
"""
import requests
url = "https://ctksv04.na1.hs-sales-engage.com/events/public/v1/encoded/track/tc/GE+23284/cTksv04/Jll2-6qcW7Y8-PT6lZ3nDW7R4C-P1wdnT8W70Sgb94dKxCCW1FYjLT6WXrPwW8QbTpt28hyz_W1t1gPc1X6HhZW2cmn6-57LhS9W7H57q24q8RHYW6yGzvm8yGbgLW633s5f5N-4TTW7zn4xk4-D1YFW7dHVzd5ttXvtW5xlRr68vhKrpW6byqL74qg69vW4dj3dd5nJZwpW41tTM86Gf1BFV4zxg_5nFdm9W18Vvjf5g7DMFW38Df2p148-_cW3jGN0j1Sm2CRW8mNjLL4G0Vp1W1k5WrN92mwrWW53Zd-l4FXHG2W7crY-P1BPkhSW5cZkp44j2DJmW7S_kLn43H-CTW3GJvrd3tC9NBf6cdvNF04?_ud=272725f9-dffc-47ee-b2f8-5938ab1da79a&_jss=0"
response = requests.get(url)
response.raise_for_status()

with open("communes.csv", "wb") as f:
    f.write(response.content)

print("Fichier téléchargé")
"""

# Chemin vers le fichier CSV
csv_path = os.path.join(os.path.dirname(__file__), "communes.csv")
df = pd.read_csv(csv_path, dtype=str)

df_final = df[["nom_standard", "code_postal"]].copy()
df_final.rename(columns={"nom_standard": "nom_commune_complet"}, inplace=True)
df_final["nom_commune_complet"] = df_final["nom_commune_complet"].str.upper()

df_final['code_postal'] = df_final['code_postal'].astype(str)
def extraire_departement(code_postal):
    if code_postal.startswith(('97', '98')):
        return code_postal[:3]
    else:
        return code_postal[:2]

df_final['departement'] = df_final['code_postal'].apply(extraire_departement)

def load_data_to_database(df):
    #Charge les données du DataFrame dans la base de données
    db = SessionLocal()
    try:
        # Insertion des données
        communes_a_inserer = []
        for _, row in df.iterrows():
            commune = Commune(
                code_postal=row['code_postal'],
                nom_complet=row['nom_commune_complet'],
                departement=row['departement']
            )
            communes_a_inserer.append(commune)
        
        # Insertion en lot pour de meilleures performances
        db.add_all(communes_a_inserer)
        db.commit()
        
        print(f"{len(communes_a_inserer)} communes insérées avec succès")
        
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de l'insertion : {e}")
        raise
    finally:
        db.close()

# Exécuter le pipeline complet
if __name__ == "__main__":
    print("Début du pipeline ETL...")
    print(f"{len(df_final)} communes à traiter")
    
    # Charger les données dans la base
    load_data_to_database(df_final)
    
    print("Pipeline ETL terminé avec succès")