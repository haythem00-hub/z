from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration MySQL (XAMPP)
DATABASE_URL = "mysql+mysqlconnector://root:@localhost/avocat"  
# ⚠️ Change test_db par le nom de ta base

# Connexion à la base
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Création de l'app FastAPI
app = FastAPI()

# Modèle pour les données reçues
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/login")
async def login(data: LoginRequest):
    db = SessionLocal()
    email = data.email
    password = data.password

    if not email or not password:
        raise HTTPException(status_code=400, detail="L'e-mail ou le mot de passe est manquant")

    try:
        # Récupérer l'utilisateur
        user = db.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": email}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        # Comparer le mot de passe
        if password != user.password:
            raise HTTPException(status_code=401, detail="Mot de passe incorrect")

        # Mettre à jour la date de dernière connexion
        last_login = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute(
            text("UPDATE users SET last_login = :last_login WHERE id = :id"),
            {"last_login": last_login, "id": user.id}
        )
        db.commit()

        return {
            "status": "success",
            "message": "Connexion réussie",
            "userData": {
                "id": user.id,
                "email": user.email,
                "created_at": str(user.created_at),
                "last_login": last_login,
                "is_active": user.is_active,
                "role": user.role
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur base de données : {str(e)}")
    finally:
        db.close()
