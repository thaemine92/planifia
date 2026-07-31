import json
import os
from pathlib import Path
from dotenv import load_dotenv
from mistralai.client import Mistral
from tools import available_tools

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
            "name": "verifier_disponibilite",
            "description": "Vérifie si une date et une heure de rendez-vous sont disponibles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_time": {
                        "type": "string",
                        "description": "La date et l'heure au format AAAA-MM-JJ HH:MM",
                    }
                },
                "required": ["date_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "prendre_rendez_vous",
            "description": "Enregistre officiellement un rendez-vous.",
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
            "description": "Affiche la liste de tous les rendez-vous enregistrés.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


def executer_agent(messages_historique):
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=messages_historique,
        tools=tools_definition,
        tool_choice="auto",
    )

    response_message = response.choices[0].message

    if response_message.tool_calls:
        messages_historique.append(response_message)

        for tool_call in response_message.tool_calls:
            fonction_nom = tool_call.function.name
            try:
                fonction_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                fonction_args = {}

            if fonction_nom in available_tools:
                try:
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

    return response_message.content