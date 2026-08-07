import uuid
import streamlit as st
import requests
import json

# Configuration de la page
st.set_page_config(page_title="Planifia - Connexion", page_icon="🔐", layout="centered")

# Adresse de l'API
API_URL = "http://127.0.0.1:8000"


def login_page():
    """Page de connexion."""
    st.title("🔐 Connexion à Planifia")
    
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur", placeholder="Entrez votre nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.form_submit_button("🔑 Se connecter"):
                try:
                    response = requests.post(
                        f"{API_URL}/login",
                        json={"username": username, "password": password}
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.token = result["token"]
                        st.session_state.user = result["user"]
                        st.session_state.logged_in = True
                        st.success(f"Connecté en tant que {result['user']['full_name']} ({result['user']['role']})")
                        st.rerun()
                    else:
                        st.error("Identifiants invalides")
                except Exception as e:
                    st.error(f"Erreur de connexion: {str(e)}")
        
        with col2:
            if st.form_submit_button("🆕 Créer un compte"):
                st.session_state.show_register = True
                st.rerun()
    
    if st.session_state.get("show_register", False):
        register_page()


def register_page():
    """Page d'inscription."""
    st.title("📝 Inscription")
    
    with st.form("register_form"):
        full_name = st.text_input("Nom complet")
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        confirm_password = st.text_input("Confirmer le mot de passe", type="password")
        role = st.selectbox("Rôle", ["patient", "medecin"])
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.form_submit_button("📤 S'inscrire"):
                if password != confirm_password:
                    st.error("Les mots de passe ne correspondent pas")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/register",
                            json={
                                "username": username,
                                "password": password,
                                "full_name": full_name,
                                "role": role
                            }
                        )
                        if response.status_code == 200:
                            st.success("Compte créé avec succès ! Vous pouvez maintenant vous connecter.")
                            st.session_state.show_register = False
                            st.rerun()
                        else:
                            st.error(f"Erreur: {response.json().get('detail', 'Erreur inconnue')}")
                    except Exception as e:
                        st.error(f"Erreur d'inscription: {str(e)}")
        
        with col2:
            if st.form_submit_button("← Retour"):
                st.session_state.show_register = False
                st.rerun()


def chat_page():
    """Page de chat principale."""
    st.title("📅 Planifia - Assistant de Rendez-vous")
    
    # Afficher les infos utilisateur
    user_info = st.session_state.get("user", {})
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.info(f"Connecté: {user_info.get('full_name', 'Inconnu')} | Rôle: {user_info.get('role', 'inconnu')}")
    with col2:
        if st.button("🔄 Rafraîchir"):
            st.rerun()
    with col3:
        if st.button("🔚 Déconnexion"):
            try:
                token = st.session_state.get("token")
                if token:
                    requests.post(f"{API_URL}/logout?token={token}")
            except:
                pass
            st.session_state.logged_in = False
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
    
    st.write("Discutez avec votre agent pour gérer vos rendez-vous.")
    
    # Initialisation de l'historique des messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # Affichage de l'historique des messages
    for message in st.session_state.messages:
        if isinstance(message, dict) and message.get("role") != "system":
            with st.chat_message(message["role"]):
                st.markdown(message.get("content", ""))
    
    # Zone de saisie utilisateur
    if prompt := st.chat_input("Écrivez votre message ici..."):
        # Ajouter le message de l'utilisateur à l'historique
        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Génération de la réponse de l'agent
        with st.chat_message("assistant"):
            with st.spinner("Réflexion en cours..."):
                try:
                    token = st.session_state.get("token")
                    
                    response = requests.post(
                        f"{API_URL}/chat",
                        json={
                            "session_id": st.session_state.session_id,
                            "message": prompt,
                            "token": token
                        },
                        timeout=30  # Timeout de 30 secondes
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.markdown(result["response"])
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result["response"]
                        })
                    else:
                        st.error(f"Erreur API: {response.status_code} - {response.text}")

                except requests.exceptions.Timeout:
                    st.error("L'API ne répond pas. Vérifiez qu'elle est bien lancée (python main.py)")
                except requests.exceptions.ConnectionError:
                    st.error("Impossible de se connecter à l'API. Vérifiez l'URL et que le serveur est démarré.")
                except Exception as e:
                    st.error(f"Erreur inattendue: {str(e)}")


def main():
    """Point d'entrée principal."""
    # Initialisation
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "show_register" not in st.session_state:
        st.session_state.show_register = False
    
    # Afficher la page appropriée
    if st.session_state.logged_in:
        chat_page()
    elif st.session_state.show_register:
        register_page()
    else:
        login_page()


if __name__ == "__main__":
    main()
