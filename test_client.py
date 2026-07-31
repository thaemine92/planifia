import requests

url = "http://127.0.0.1:8000/chat"
payload = {
    "session_id": "test-1",
    "message": "Je voudrais prendre un rendez-vous demain a 14h",
}

response = requests.post(url, json=payload)
print("Resultat :")
print(response.json())