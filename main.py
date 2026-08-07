from agent import executer_agent
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
from database import UserDB, SessionLocal
import sys
import codecs
import secrets

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
app = FastAPI(title="API Agent de Rendez-vous Mistral")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

# Stockage des sessions
sessions_memoire = {}

# Stockage des sessions utilisateur (token -> user_info)
active_sessions = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "patient"


class ChatRequest(BaseModel):
    session_id: str
    message: str
    token: Optional[str] = None  # Token d'authentification


@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de l'agent de rendez-vous de Planifia !"}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authentifie un utilisateur."""
    db = SessionLocal()
    try:
        user = db.query(UserDB).filter(UserDB.username == username).first()
        if user and UserDB.verify_password(password, user.password_hash):
            return {
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role
            }
        return None
    finally:
        db.close()


@app.post("/login")
def login_endpoint(request: LoginRequest):
    """Connecte un utilisateur et retourne un token de session."""
    user_info = authenticate_user(request.username, request.password)
    if not user_info:
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    
    # Générer un token de session
    token = secrets.token_hex(32)
    active_sessions[token] = user_info
    
    return {
        "status": "success",
        "token": token,
        "user": user_info
    }


@app.post("/logout")
def logout_endpoint(token: str):
    """Déconnecte un utilisateur."""
    if token in active_sessions:
        del active_sessions[token]
        return {"status": "success", "message": "Déconnexion réussie"}
    return {"status": "error", "message": "Token invalide"}


@app.post("/register")
def register_endpoint(request: RegisterRequest):
    """Enregistre un nouvel utilisateur."""
    db = SessionLocal()
    try:
        # Vérifier si l'utilisateur existe déjà
        existing = db.query(UserDB).filter(UserDB.username == request.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà utilisé")
        
        # Création du nouvel utilisateur
        new_user = UserDB(
            username=request.username,
            password_hash=UserDB.hash_password(request.password),
            role=request.role,
            full_name=request.full_name
        )
        db.add(new_user)
        db.commit()
        
        return {
            "status": "success",
            "message": "Utilisateur créé avec succès",
            "user": {
                "username": new_user.username,
                "full_name": new_user.full_name,
                "role": new_user.role
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/me")
def get_current_user(token: str):
    """Récupère les informations de l'utilisateur connecté."""
    if token not in active_sessions:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    return {"user": active_sessions[token]}


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    try:
        session_id = request.session_id
        message_utilisateur = request.message
        token = request.token
        
        # Récupérer les infos utilisateur si token fourni
        username = None
        user_role = None
        user_full_name = None
        
        if token and token in active_sessions:
            user_info = active_sessions[token]
            username = user_info["username"]
            user_role = user_info["role"]
            user_full_name = user_info["full_name"]

        if session_id not in sessions_memoire:
            sessions_memoire[session_id] = [
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant virtuel professionnel de gestion de rendez-vous. "
                        "Tu aides à vérifier les disponibilités et à planifier des rendez-vous "
                        "en utilisant les outils mis à ta disposition."
                    ),
                }
            ]

        historique = sessions_memoire[session_id]
        historique.append({"role": "user", "content": message_utilisateur})

        reponse_ia = executer_agent(historique, username, user_role)
        historique.append({"role": "assistant", "content": reponse_ia})

        return {
            "session_id": session_id, 
            "response": reponse_ia,
            "user_role": user_role,
            "username": username
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)