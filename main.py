from urllib import request
from django import db
from fastapi import FastAPI, HTTPException
from flask import jsonify
from sqlalchemy import create_engine, text, Table, MetaData, select
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Table, MetaData, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
current_utc_time = datetime.now(timezone.utc)

# Créer une instance de l'application FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Vous pouvez spécifier un domaine si vous voulez restreindre l'accès
    allow_credentials=True,
    allow_methods=["*"],  # Autorise toutes les méthodes HTTP
    allow_headers=["*"],  # Autorise tous les en-têtes
)

# Configurer la connexion à la base de données (modifie cette URL en fonction de ta DB)
DATABASE_URL = "mysql+mysqlconnector://root:@localhost:3306/boutique"

# Créer un moteur SQLAlchemy pour se connecter à la DB
engine = create_engine(DATABASE_URL)

# Créer un objet MetaData pour la base de données
metadata = MetaData()

# Session locale pour interagir avec la base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
photo = Table('photo', metadata, autoload_with=engine)

@app.get("/listphoto/{idarticle}", response_model=dict)
def get_product_images(idarticle: int):
    db = SessionLocal()
    try:
        # Requête SQL pour récupérer les URLs des images liées à l'article
        result = db.execute(
            select(photo.c.imageUrl).where(photo.c.idarticle == idarticle)
        ).fetchall()

        if not result:
            raise HTTPException(status_code=404, detail="Aucune image trouvée pour cet article")

        # Extraction des URLs des images
        image_urls = [row[0] for row in result]  # row[0] car 'imageUrl' est la seule colonne sélectionnée

        # Retour structuré
        return {"images": image_urls}

    finally:
        db.close()

class LoginRequest(BaseModel):
    email: str
    password: str 

@app.post("/login")
async def login(data:LoginRequest):
    db = SessionLocal()
    email =data.email
    password =data.password
    if not email or not password:
        raise HTTPException(status_code=400, detail="L'e-mail ou le mot de passe est manquant")

    try:
        # Try to fetch the client from the database
        client = db.execute(text('SELECT * FROM client WHERE email = :email'), {"email": email}).fetchone()

        if client:
            # Check if the password matches
            if password == client[3]:  # Assuming the password is at index 3
                date_derniere_connexion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                historique_connexions = f"{client[13]} {date_derniere_connexion}" if client[13] else date_derniere_connexion  # index 5 for historique_connexions

                # Update the client's connection history
                update_query = text("""
                    UPDATE client
                    SET date_derniere_connexion = :date_connexion, historique_connexions = :historique 
                    WHERE id_client = :id_client
                """)
                db.execute(update_query, {
                    "date_connexion": date_derniere_connexion,
                    "historique": historique_connexions,
                    "id_client": client[0]  # Assuming id_client is at index 0
                })
                db.commit()

                return {
                    'status': 'success',
                    'message': 'client ',
                    'clientData': {
                        'id_client': str(client[0]),
                        'nom_complet': str(client[1]),  # nom_complet at index 1
                        'email': str(client[2]),
                        'mot_de_passe':client[3],# email at index 2
                        'numero_telephone': str(client[4]),  # numero_telephone at index 4
                        'adresse_livraison':str(client[5]),  # adresse_livraison at index 6
                        'adresse_facturation': str(client[6]),  # adresse_facturation at index 7
                        'date_inscription': str(client[7]),  # date_inscription at index 8
                        'historique_commandes': str(client[8]),  # historique_commandes at index 9
                        'statut_client': str(client[9]),  # statut_client at index 10
                        'preferences': str(client[10]),  # preferences at index 11
                        'methode_paiement': str(client[11]),  # methode_paiement at index 12
                        'points_fidelite': str(client[12]),  # points_fidelite at index 13
                        'date_derniere_connexion': date_derniere_connexion,
                        'historique_connexions': historique_connexions
                    }
                }
            else:
                raise HTTPException(status_code=401, detail="Mot de passe incorrect")

        # Check in the admins table
        admin_query = text("SELECT * FROM admins WHERE email = :email")
        admin = db.execute(admin_query, {"email": email}).fetchone()

        if admin:
            if password == admin[2]:  # Assuming password is at index 2 for admins
                return {'status': 'success', 'message': 'admin ', 'email': email}
            else:
                raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

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
    try:
        # Créer une session de base de données
        db= SessionLocal()

        # Charger les tables dynamiquement
        article = Table('article', metadata, autoload_with=engine)
        categorie = Table('categorie', metadata, autoload_with=engine)

        # Effectuer une jointure entre 'article' et 'categorie'
        
        stmt = select(
            article.c.idarticle,
            article.c.libarticle,
            article.c.prix,
            article.c.quantite,
            article.c.description,
            article.c.idcategorie,
            article.c.imageUrl,
            article.c.couleur,
            categorie.c.libcategorie.label("categorie") , # On sélectionne seulement le nom de la catégorie
        ).join(categorie, article.c.idcategorie == categorie.c.idcategorie)


        # Exécuter la requête
        result = db.execute(stmt).fetchall()

        # Convertir chaque ligne en dictionnaire
        produits = [dict(row._mapping) for row in result]

        return produits

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()
@app.get("/fetchcom/{id}")
def get_commentaire(id: int):
    try:
        # Créer une session de base de données
        db= SessionLocal()

        # Charger les tables dynamiquement
        article = Table('commentaire', metadata, autoload_with=engine)
        stmt = select(
            article.c.commentaire,
        ).where(article.c.idarticle == id)
        # Exécuter la requête
        result = db.execute(stmt).fetchall()

        # Convertir chaque ligne en dictionnaire
        produits = [dict(row._mapping) for row in result]

        return produits

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()

@app.get("/categorie")
def get_produits():
    try:
        # Créer une session de base de données
        db= SessionLocal()

        # Charger les tables dynamiquement
        categorie = Table('categorie', metadata, autoload_with=engine)

        # Effectuer une jointure entre 'article' et 'categorie'
        
        stmt = select(
            categorie.c.idcategorie,
            categorie.c.libcategorie,
            categorie.c.catUrl,
        )


        # Exécuter la requête
        result = db.execute(stmt).fetchall()

        # Convertir chaque ligne en dictionnaire
        produits = [dict(row._mapping) for row in result]

        return produits

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()

class ProductRequest(BaseModel):
    id: str 

@app.delete("/delete")
async def delete_product(data: ProductRequest):
    db= SessionLocal()  # Ouvre une session à la base de données
    try:
        query = text("SELECT * FROM article WHERE idarticle = :id")
        result = db.execute(query, {"id": int(data.id)}).fetchone()
        if result[0]==0:
            return {"status": "error", "message": "P,existe pas"}
        a=text("DELETE FROM article WHERE idarticle = :id")
        db.execute( a, {"id": int(result[0])})
        db.commit()

        return {"status": "success", "message": "Produit supprimé avec succès"}


    finally:
        db.close()  # Fermer la session à la base de données
class ProductRequest1(BaseModel):
    name: str
    price: str
    quantity: str
    color: str
    description: str
    imageUrl: str
    idcategorie: int

@app.post("/add")
async def add_product(data: ProductRequest1):
    db = SessionLocal()  # Ouvre une session à la base de données
    try:
        # Insertion du nouveau produit
        insert_query = text("""
            INSERT INTO article (libarticle, prix, quantite, couleur, description, imageUrl, idcategorie)
            VALUES (:name, :price, :quantity, :color, :description, :imageUrl, :idcategorie)
        """)

        db.execute(insert_query, {
            "name": data.name,
            "price": data.price,
            "quantity": data.quantity,
            "color": data.color,
            "description": data.description,
            "imageUrl": data.imageUrl,
            "idcategorie": data.idcategorie
        })
        db.commit()

        return {"status": "success", "message": "Produit ajouté avec succès"}

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        db.close()
# Modèle de la requête
class CommentRequest(BaseModel):
    id_client: str
    idarticle: str
    commentaire: str

@app.post("/add_comment")
async def add_comment(data: CommentRequest):
    db = SessionLocal()  # Ouvre une session à la base de données
    try:
        # Insertion du commentaire
        insert_query = text("""
            INSERT INTO commentaire (id_client, idarticle, commentaire)
            VALUES (:id_client, :idarticle, :commentaire)
        """)

        db.execute(insert_query, {
            "id_client": data.id_client,
            "idarticle": data.idarticle,
            "commentaire": data.commentaire
        })
        db.commit()

        return {"status": "success", "message": "Commentaire ajouté avec succès"}

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        db.close()  # Ferme la session à la base de données
class CartRequest(BaseModel):
    id_client: str
    idarticle: str
    qte: str

@app.post("/add_to_cart")
async def add_to_cart(data: CartRequest):
    db = SessionLocal()  # Ouvre une session à la base de données
    try:
        # Insertion dans le panier
        insert_query = text("""
            INSERT INTO panier (id_client, idarticle, qte)
            VALUES (:id_client, :idarticle, :qte)
        """)

        db.execute(insert_query, {
            "id_client": data.id_client,
            "idarticle": data.idarticle,
            "qte": data.qte
        })
        db.commit()

        return {"status": "success", "message": "Produit ajouté avec succès au panier."}

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        db.close()  # Ferme la session à la base de données
class ClientUpdateRequest(BaseModel):
    idClient: int
    nomComplet: str
    email: str
    motDePasse: str
    numeroTelephone: str = None
    adresseLivraison: str = None
    adresseFacturation: str = None
    dateInscription: str = None
    historiqueCommandes: str = None
    statutClient: str = None
    preferences: str = None
    methodePaiement: str = None
    pointsFidelite: int = 0
    dateDerniereConnexion: str = None
    historiqueConnexions: str = None

@app.put("/update_client")
async def update_client(client_data: ClientUpdateRequest):
    db = SessionLocal()  # Ouvre une session à la base de données
    try:
        # Préparer la requête SQL pour mettre à jour les données du client
        update_query = text("""
            UPDATE client SET 
                nom_complet = :nomComplet,
                email = :email,
                mot_de_passe = :motDePasse,
                numero_telephone = :numeroTelephone,
                adresse_livraison = :adresseLivraison,
                adresse_facturation = :adresseFacturation,
                date_inscription = :dateInscription,
                historique_commandes = :historiqueCommandes,
                statut_client = :statutClient,
                preferences = :preferences,
                methode_paiement = :methodePaiement,
                points_fidelite = :pointsFidelite,
                date_derniere_connexion = :dateDerniereConnexion,
                historique_connexions = :historiqueConnexions
            WHERE id_client = :idClient
        """)

        db.execute(update_query, client_data.dict())
        db.commit()

        return {"status": "success", "message": "Client mis à jour avec succès"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")

    finally:
        db.close() 
 
class ClientUpdateRequest(BaseModel):
    nom_complet: str
    email: str
    mot_de_passe: str
    numero_telephone: str
    adresse_livraison: str
    adresse_facturation: str
    date_inscription: str
    historique_commandes: str
    statut_client: str
    preferences: str
    methode_paiement: str
    points_fidelite: int
    date_derniere_connexion: str
    historique_connexions: str

@app.post("/register")
async def register_client(client_data: ClientUpdateRequest):
    db = SessionLocal()  # Ouvre une session à la base de données
    try:
        # Préparer la requête SQL pour insérer les données du client
        insert_query = text("""
            INSERT INTO client (
                nom_complet, email, mot_de_passe, numero_telephone, 
                adresse_livraison, adresse_facturation, date_inscription, 
                historique_commandes, statut_client, preferences, 
                methode_paiement, points_fidelite, date_derniere_connexion, 
                historique_connexions
            ) 
            VALUES (
                :nomComplet, :email, :motDePasse, :numeroTelephone, 
                :adresseLivraison, :adresseFacturation, :dateInscription, 
                :historiqueCommandes, :statutClient, :preferences, 
                :methodePaiement, :pointsFidelite, :dateDerniereConnexion, 
                :historiqueConnexions
            )
        """)

        # Exécuter la requête avec les données du client
        db.execute(insert_query, client_data.dict())
        db.commit()

        return {"status": "success", "message": "Client inscrit avec succès"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Erreur lors de l'inscription : {str(e)}"}
    finally:
        db.close()
