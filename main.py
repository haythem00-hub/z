from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Table, MetaData, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware

# Créer une instance FastAPI
app = FastAPI()

# Autoriser toutes les origines (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL de connexion à la base de données
DATABASE_URL = "mysql+mysqlconnector://boutikti_boutique:Haythem00@localhost:3306/boutikti_boutique"

# Moteur SQLAlchemy
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Session locale
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ➤ Route racine qui renvoie un message
@app.get("/")
def home():
    return {"message": "123"}

@app.get("/produits/{id}")
def get_produit(id: int):
    db = SessionLocal()
    try:
        article = Table('article', metadata, autoload_with=engine)
        result = db.execute(article.select().where(article.c.idarticle == id)).fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail="Produit non trouvé")
        return dict(result._mapping)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=503, detail=str(e))
    finally:
        db.close()

@app.get("/produits")
def get_produits():
    db = SessionLocal()
    try:
        # Charger les tables
        article = Table('article', metadata, autoload_with=engine)
        categorie = Table('categorie', metadata, autoload_with=engine)

        # Jointure entre article et categorie
        stmt = select(
            article.c.idarticle,
            article.c.libarticle,
            article.c.prix,
            article.c.quantite,
            article.c.description,
            article.c.idcategorie,
            article.c.imageUrl,
            article.c.couleur,
            categorie.c.libcategorie.label("categorie")
        ).join(categorie, article.c.idcategorie == categorie.c.idcategorie)

        result = db.execute(stmt).fetchall()
        return [dict(row._mapping) for row in result]

    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
