from agent import executer_agent
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import codecs

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
app = FastAPI(title="API Agent de Rendez-vous Mistral")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions_memoire = {}


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de l'agent de rendez-vous de Planifia !"}


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    try:
        session_id = request.session_id
        message_utilisateur = request.message

        if session_id not in sessions_memoire:
            sessions_memoire[session_id] = [
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant virtuel professionnel de gestion de rendez-vous. "
                        "Tu aides les clients à vérifier les disponibilités et à planifier des rendez-vous "
                        "en utilisant les outils mis à ta disposition."
                    ),
                }
            ]

        historique = sessions_memoire[session_id]
        historique.append({"role": "user", "content": message_utilisateur})

        reponse_ia = executer_agent(historique)
        historique.append({"role": "assistant", "content": reponse_ia})

        return {"session_id": session_id, "response": reponse_ia}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)