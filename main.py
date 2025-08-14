from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error

app = FastAPI()

# Autoriser toutes les origines et méthodes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connexion MySQL
def get_connection():
    try:
        return mysql.connector.connect(
            host="boutikti.online",
            user="boutikti_boutique",
            password="Haythem00",
            database="boutikti_avocat"
        )
    except Error as e:
        print("Erreur de connexion MySQL:", e)
        return None

# Modèle Login
class LoginData(BaseModel):
    username: str
    password: str

# Route GET
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

# Route POST
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

    if user and data.password == user["password"]:  # À remplacer par un hash bcrypt
        return {
            "success": True,
            "message": "Login successful",
            "user": user
        }
    else:
        return {"success": False, "message": "Invalid credentials"}
