from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Commune(Base):
    __tablename__ = "communes"
    id = Column(Integer, primary_key=True)
    code_postal = Column(String(5), nullable=False, index=True)
    nom_complet = Column(String(100), nullable=False)
    departement = Column(String(3), nullable=False, index=True)
