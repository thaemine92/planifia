import json
import os
from pathlib import Path
from dotenv import load_dotenv
from mistralai.client import Mistral
from tools import available_tools, get_user_info

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("MISTRAL_API_KEY")
if api_key:
    api_key = api_key.strip()

client = Mistral(api_key=api_key)

tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "verifier_creneau_disponible",
            "description": "Vérifie si un créneau horaire spécifique est libre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_time": {
                        "type": "string",
                        "description": "Date et heure au format AAAA-MM-JJ HH:MM",
                    }
                },
                "required": ["date_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verifier_disponibilite_journee",
            "description": "Vérifie les disponibilités pour une journée entière.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "La date cible au format AAAA-MM-JJ",
                    }
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "prendre_rendez_vous",
            "description": "Enregistre officiellement un rendez-vous. Pour les médecins, le doctor_name sera automatiquement défini.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string", "description": "Nom du client"},
                    "date_time": {
                        "type": "string",
                        "description": "Date et heure du rendez-vous au format AAAA-MM-JJ HH:MM",
                    },
                    "service": {
                        "type": "string",
                        "description": "Type de service demandé",
                    },
                    "doctor_name": {
                        "type": "string",
                        "description": "Nom du médecin (optionnel)",
                    },
                },
                "required": ["client_name", "date_time", "service"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "annuler_rendez_vous",
            "description": "Annule un rendez-vous existant pour un client à une date précise.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string", "description": "Nom du client"},
                    "date_time": {"type": "string", "description": "Date et heure du rendez-vous à annuler"},
                },
                "required": ["client_name", "date_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lister_rendez_vous",
            "description": "Liste les rendez-vous pour un client ou un médecin spécifique.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string", "description": "Nom du client pour filtrer (optionnel)"},
                    "doctor_name": {"type": "string", "description": "Nom du médecin pour filtrer (optionnel)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lister_tous_rendez_vous",
            "description": "Liste tous les rendez-vous du système (réservé aux médecins).",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lister_patients",
            "description": "Liste tous les patients du système (réservé aux médecins).",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lister_medecins",
            "description": "Liste tous les médecins disponibles.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


def executer_agent(messages_historique, username: str = None, user_role: str = None):
    # Récupérer les infos utilisateur une seule fois
    user_info = None
    if username and user_role:
        user_info = get_user_info(username)
        
        # Si on a les infos utilisateur, enrichir le contexte
        if user_info:
            # Ajouter le contexte utilisateur comme premier message si ce n'est pas déjà fait
            context_exists = any(
                msg.get("role") == "system" and 
                (user_info["full_name"] in msg.get("content", "") or user_info["role"] in msg.get("content", ""))
                for msg in messages_historique
            )
            
            if not context_exists:
                # Créer un message système personnalisé avec le contexte utilisateur
                system_message = {
                    "role": "system",
                    "content": (
                        f"Tu es un assistant virtuel professionnel de gestion de rendez-vous. "
                        f"L'utilisateur actuel est {user_info['full_name']} avec le rôle de {user_info['role']}. "
                        f"Tu aides à vérifier les disponibilités, à planifier, à lister "
                        f"et à annuler des rendez-vous. "
                        f"Si l'utilisateur est un patient, ne montre que SES rendez-vous. "
                        f"Si c'est un médecin, il peut voir tous les rendez-vous et gérer ses patients."
                    )
                }
                # Remplacer ou ajouter le message système
                messages_historique = [
                    msg for msg in messages_historique 
                    if not (msg.get("role") == "system" and "assistant virtuel" in msg.get("content", ""))
                ]
                messages_historique.insert(0, system_message)
    
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=messages_historique,
        tools=tools_definition,
        tool_choice="auto",
    )

    response_message = response.choices[0].message

    if response_message.tool_calls:
        # Convertir l'objet message en dictionnaire avant de l'ajouter
        assistant_message_dict = {
            "role": "assistant",
            "content": response_message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in response_message.tool_calls
            ]
        }
        messages_historique.append(assistant_message_dict)

        for tool_call in response_message.tool_calls:
            fonction_nom = tool_call.function.name
            try:
                fonction_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                fonction_args = {}

            if fonction_nom in available_tools:
                try:
                    # Pour certaines fonctions, injecter automatiquement le nom de l'utilisateur
                    if fonction_nom in ["lister_rendez_vous", "prendre_rendez_vous", "annuler_rendez_vous"]:
                        if user_role == "patient" and username and "client_name" not in fonction_args:
                            fonction_args["client_name"] = user_info.get("full_name", username) if user_info else username
                        elif user_role == "medecin" and username and user_info:
                            # Pour un médecin, on peut remplir doctor_name automatiquement
                            if "doctor_name" not in fonction_args:
                                fonction_args["doctor_name"] = user_info.get("full_name", username)
                    
                    # Exécution sécurisée de l'outil
                    resultat_fonction = available_tools[fonction_nom](**fonction_args)
                except Exception as e:
                    # Si l'outil plante, on renvoie l'erreur à l'IA pour qu'elle s'adapte
                    resultat_fonction = {"status": "error", "message": f"Erreur lors de l'exécution : {str(e)}"}

                messages_historique.append(
                    {
                        "role": "tool",
                        "name": fonction_nom,
                        "content": json.dumps(resultat_fonction),
                        "tool_call_id": tool_call.id,
                    }
                )

        final_response = client.chat.complete(
            model="mistral-small-latest", messages=messages_historique
        )
        return final_response.choices[0].message.content

    # Convertir la réponse simple en dictionnaire
    return response_message.content