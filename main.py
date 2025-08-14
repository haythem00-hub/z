from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import json

# -----------------------------
# Configuration FastAPI + CORS
# -----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Autoriser toutes les origines
    allow_methods=["*"],      # Autoriser toutes les méthodes (GET, POST, etc.)
    allow_headers=["*"],      # Autoriser tous les headers
)

# -----------------------------
# Modèle pour recevoir les données JSON
# -----------------------------
class LoginData(BaseModel):
    username: str
    password: str
class RegisterUser(BaseModel):
    username: str
    email: str
    phone: str
    password: str

# -----------------------------
# Connexion à la base MySQL
# -----------------------------
def get_connection():
    try:
        conn = mysql.connector.connect(
            host="boutikti.online",       # Remplace par ton domaine
            user="boutikti_boutique",
            password="Haythem00",
            database="boutikti_avocat"
        )
        return conn
    except Error as e:
        print("Erreur de connexion MySQL:", e)
        return None

# -----------------------------
# Route pour récupérer tous les utilisateurs
# -----------------------------
@app.get("/")
async def get_all_users():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection error")

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return {"success": True, "users": users}

# -----------------------------
# Route de connexion (login)
# -----------------------------
@app.post("/login")
async def login(request: Request):
    try:
        # Lecture du JSON brut
        raw_body = await request.body()
        data_dict = json.loads(raw_body.decode("utf-8"))

        # Validation via Pydantic
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
    cursor.execute("SELECT * FROM users WHERE username = %s", (data.username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and data.password == user["password"]:  # Comparaison en clair (à remplacer par un hash)
        return {
            "success": True,
            "message": "Login successful",
            "user": user
        }
    else:
        return {"success": False, "message": "Invalid credentials"}
@app.post("/register")
async def register(request: Request):
    try:
        raw_body = await request.body()
        data_dict = json.loads(raw_body.decode("utf-8"))
        user = RegisterUser(**data_dict)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except TypeError:
        raise HTTPException(status_code=400, detail="Invalid data structure")

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection error")

    cursor = conn.cursor(dictionary=True)

    # Vérifier si l'utilisateur existe déjà
    cursor.execute("SELECT * FROM users WHERE username = %s", (user.username,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return {"success": False, "message": "Username already exists"}

    # Insérer l'utilisateur
    try:
        cursor.execute(
            "INSERT INTO users (username, email, phone, password) VALUES (%s, %s, %s, %s)",
            (user.username, user.email, user.phone, user.password)
        )
        conn.commit()
        return {"success": True, "message": "Registration successful"}
    except Error as e:
        print("Erreur insertion:", e)
        raise HTTPException(status_code=500, detail="Erreur lors de l'inscription")
    finally:
        cursor.close()
        conn.close()        
