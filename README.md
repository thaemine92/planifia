# Planifia - Système de Gestion de Rendez-vous avec IA

Un système complet de gestion de rendez-vous médecins-patients utilisant l'IA Mistral.

## Fonctionnalités

- **Gestion des utilisateurs** : Patients et médecins avec authentification
- **Gestion des rendez-vous** : Prise, annulation, liste des rendez-vous
- **Filtrage intelligent** : Chaque utilisateur voit uniquement ses propres rendez-vous
- **Interface IA** : Conversation naturelle avec l'assistant pour gérer les rendez-vous
- **Deux interfaces** : Streamlit (pour les tests) et FastAPI (pour le déploiement)

## Structure du projet

```
planifia/
├── app.py          # Interface Streamlit (version basique)
├── app_auth.py     # Interface Streamlit avec authentification
├── main.py         # API FastAPI
├── agent.py        # Agent IA avec outils Mistral
├── tools.py        # Fonctions outils pour la gestion des rendez-vous
├── database.py     # Base de données SQLite et modèles
├── README.md        # Ce fichier
└── .env            # Configuration (clé API Mistral)
```

## Prérequis

- Python 3.8+
- pip
- Compte Mistral AI avec clé API

## Installation

1. **Créer un environnement virtuel** :
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.\.venv\Scripts\activate  # Windows
```

2. **Installer les dépendances** :
```bash
pip install fastapi uvicorn streamlit requests python-dotenv sqlalchemy mistralai
```

3. **Configurer l'API Mistral** :
Créer un fichier `.env` dans le répertoire du projet :
```
MISTRAL_API_KEY=votre_clé_api_mistral
```

## Utilisation

### Méthode 1 : API FastAPI + Interface Streamlit

1. **Lancer l'API** :
```bash
python main.py
```
L'API sera accessible sur `http://127.0.0.1:8000`

2. **Dans un autre terminal, lancer l'interface Streamlit** :
```bash
streamlit run app_auth.py
```
L'interface sera accessible sur `http://localhost:8501`

3. **Utilisateurs par défaut** (créés automatiquement) :
   - Médecin: `dr.yohan` / `password123`
   - Patient: `lewis` / `password123`


### Endpoints API

- `GET /` : Accueil
- `POST /login` : Connexion (username, password)
- `POST /register` : Inscription (username, password, full_name, role)
- `POST /logout` : Déconnexion (token)
- `GET /me` : Infos utilisateur (token)
- `POST /chat` : Discussion avec l'AIA (session_id, message, token)

## Exemples de conversation

### Pour un patient :
```
Patient: "Bonjour, je veux prendre un rendez-vous pour demain à 10h"
IA: "Quel type de service souhaitez-vous ?"
Patient: "Consultation"
IA: "Rendez-vous enregistré pour Lewis Hamilton le 2026-08-07 à 10:00 pour une consultation"
```

### Pour un médecin :
```
Médecin: "Quels sont mes rendez-vous aujourd'hui ?"
IA: "Vous avez 3 rendez-vous aujourd'hui: ..."

Médecin: "Liste tous les patients"
IA: "Voici la liste de tous les patients: ..."
```

## Base de données

Le système utilise SQLite avec les tables suivantes :
- `users` : Utilisateurs (patients et médecins)
- `rendez_vous` : Rendez-vous

La base de données est créée automatiquement au premier lancement.

## Personnalisation

### Ajouter un nouvel outil
1. Ajouter la fonction dans `tools.py`
2. Ajouter la définition dans `tools_definition` dans `agent.py`
3. Ajouter le nom dans `available_tools`

### Modifier le comportement de l'IA
Modifier le message système dans `executer_agent()` dans `agent.py` ou dans les endpoints API.

## Sécurité

- Les mots de passe sont hachés avec SHA256
- Les tokens de session sont générés aléatoirement
- Chaque utilisateur ne voit que ses propres données

## Déploiement

Pour le déploiement en production :
1. Utiliser un serveur ASGI comme Uvicorn avec Gunicorn
2. Configurer un reverse proxy (Nginx)
3. Utiliser HTTPS
4. Externaliser la base de données (PostgreSQL, MySQL)

## Contributeurs

- Yohan - Développeur principal

## Licence

MIT
