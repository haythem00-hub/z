from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error

# -----------------------------
# CORS (équivalent des headers PHP)
# -----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # équivalent de Access-Control-Allow-Origin: *
    allow_methods=["POST"],  # équivalent de Access-Control-Allow-Methods: POST
    allow_headers=["Content-Type"],  # équivalent de Access-Control-Allow-Headers: Content-Type
)

# -----------------------------
# Modèle pour recevoir les données JSON
# -----------------------------
class LoginData(BaseModel):
    username: str
    password: str

# -----------------------------
# Connexion à la base MySQL
# -----------------------------
def get_connection():
    try:
        conn = mysql.connector.connect(
            host="boutikti.online",        # remplace par ton domaine
            user="boutikti_boutique",
            password="Haythem00",
            database="boutikti_avocat"
        )
        return conn
    except Error as e:
        print("Erreur de connexion MySQL:", e)
        return None

# -----------------------------
# Endpoint POST /login
# -----------------------------
@app.post("/login")
async def login(data: LoginData):
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

    if user and data.password == user["password"]:  # comparaison en clair
        return {
            "success": True,
            "message": "Login successful",
            "user": user
        }
    else:
        return {"success": False, "message": "Invalid credentials"}
