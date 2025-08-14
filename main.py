from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import mysql.connector
from mysql.connector import Error
from passlib.hash import bcrypt
import json

# -----------------------------
# Configuration FastAPI + CORS
# -----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pour dev, en production mettre le domaine Flutter
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Modèles Pydantic
# -----------------------------
class RegisterUser(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str

class LoginData(BaseModel):
    username: str
    password: str

# -----------------------------
# Connexion MySQL
# -----------------------------
def get_connection():
    try:
        conn = mysql.connector.connect(
            host="boutikti.online",
            user="boutikti_boutique",
            password="Haythem00",
            database="boutikti_avocat"
        )
        return conn
    except Error as e:
        print("Erreur de connexion MySQL:", e)
        return None

# -----------------------------
# Liste des utilisateurs
# -----------------------------
@app.get("/")
async def get_all_users():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection error")

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, phone FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return {"success": True, "users": users}

# -----------------------------
# Route d'inscription
# -----------------------------
@app.post("/register")
async def register(user: RegisterUser):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection error")

    cursor = conn.cursor()

    # Vérifier si l'email existe déjà
    cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    # Hasher le mot de passe
    hashed_password = bcrypt.hash(user.password)

    try:
        cursor.execute(
            "INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)",
            (user.name, user.email, user.phone, hashed_password)
        )
        conn.commit()
        return {"success": True, "message": "Inscription réussie !"}
    except Error as e:
        print("Erreur insertion:", e)
        raise HTTPException(status_code=500, detail="Erreur lors de l'inscription")
    finally:
        cursor.close()
        conn.close()

# -----------------------------
# Route de connexion
# -----------------------------
@app.post("/login")
async def login(request: Request):
    try:
        raw_body = await request.body()
        data_dict = json.loads(raw_body.decode("utf-8"))
        data = LoginData(**data_dict)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except TypeError:
        raise HTTPException(status_code=400, detail="Invalid data structure")

    if not data.username or not data.password:
        return {"success": False, "message": "Missing username or password"}

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection error")

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (data.username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and bcrypt.verify(data.password, user["password"]):
        # Ne jamais renvoyer le mot de passe dans la réponse
        user_info = {k: v for k, v in user.items() if k != "password"}
        return {
            "success": True,
            "message": "Login successful",
            "user": user_info
        }
    else:
        return {"success": False, "message": "Invalid credentials"}
