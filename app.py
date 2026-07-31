import uuid
import streamlit as st
from agent import executer_agent

# Configuration de la page
st.set_page_config(page_title="Planifia - Assistant de Rendez-vous", page_icon="📅", layout="centered")

st.title("📅 Planifia - Assistant Virtuel")
st.write("Discutez avec votre agent pour gérer vos rendez-vous.")

if st.sidebar.button("🔄 Nouvelle conversation"):
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "Tu es un assistant virtuel professionnel de gestion de rendez-vous. "
                "Tu aides les clients à vérifier les disponibilités, à planifier, à lister "
                "et à annuler des rendez-vous en utilisant les outils mis à ta disposition."
            ),
        }
    ]
    st.rerun()

# Initialisation d'un identifiant de session unique pour l'utilisateur dans le navigateur
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Initialisation de l'historique des messages dans l'état de Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "Tu es un assistant virtuel professionnel de gestion de rendez-vous. "
                "Tu aides les clients à vérifier les disponibilités, à planifier, à lister "
                "et à annuler des rendez-vous en utilisant les outils mis à ta disposition."
            ),
        }
    ]

# Affichage de l'historique des messages (en ignorant le message système initial)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if isinstance(message, dict) and message.get("role") != "system":
        with st.chat_message(message["role"]):
            st.markdown(message.get("content", ""))

# Zone de saisie utilisateur en bas de page
if prompt := st.chat_input("Écrivez votre message ici..."):
    # Ajouter le message de l'utilisateur à l'historique
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Génération de la réponse de l'agent
    with st.chat_message("assistant"):
        with st.spinner("Réflexion en cours..."):
            try:
                # On passe une copie ou l'historique filtré de dictionnaires à l'agent
                reponse_ia = executer_agent(st.session_state.messages)
                st.markdown(reponse_ia)
                # Ajout de la réponse sous forme de dico pur
                st.session_state.messages.append({"role": "assistant", "content": reponse_ia})
            except Exception as e:
                st.error(f"Erreur : {str(e)}")