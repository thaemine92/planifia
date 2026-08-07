from database import RendezVousDB, UserDB, SessionLocal
from typing import Optional, List


def get_user_info(username: str) -> Optional[dict]:
    """Récupère les informations d'un utilisateur."""
    db = SessionLocal()
    try:
        user = db.query(UserDB).filter(UserDB.username == username).first()
        if user:
            return {
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role
            }
        return None
    finally:
        db.close()


def prendre_rendez_vous(client_name: str, date_time: str, service: str, doctor_name: Optional[str] = None):
    """Réserve un nouveau rendez-vous dans le système."""
    db = SessionLocal()
    try:
        if doctor_name:
            nouveau_rdv = RendezVousDB(
                client_name=client_name, 
                doctor_name=doctor_name,
                date_time=date_time, 
                service=service
            )
        else:
            nouveau_rdv = RendezVousDB(
                client_name=client_name, 
                date_time=date_time, 
                service=service
            )
        
        db.add(nouveau_rdv)
        db.commit()
        return {
            "status": "success",
            "message": f"Rendez-vous bien enregistré pour {client_name} le {date_time}{' avec Dr. ' + doctor_name if doctor_name else ''}.",
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def verifier_creneau_disponible(date_time: str):
    """Vérifie si un créneau horaire est libre."""
    db = SessionLocal()
    try:
        existant = (
            db.query(RendezVousDB).filter(RendezVousDB.date_time == date_time).first()
        )
        if existant:
            return {"disponible": False, "message": f"Ce créneau est déjà pris par {existant.client_name}."}
        return {"disponible": True, "message": "Le créneau est libre."}
    finally:
        db.close()

def annuler_rendez_vous(client_name: str, date_time: str):
    """Annule un rendez-vous en fonction de la date et du nom du client."""
    db = SessionLocal()
    try:
        rdv = (
            db.query(RendezVousDB)
            .filter(RendezVousDB.client_name == client_name, RendezVousDB.date_time == date_time)
            .first()
        )
        if rdv:
            db.delete(rdv)
            db.commit()
            return {"status": "success", "message": f"Le rendez-vous de {client_name} prévu le {date_time} a bien été annulé."}
        return {"status": "error", "message": "Aucun rendez-vous trouvé pour ces informations."}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

def lister_rendez_vous(client_name: Optional[str] = None, doctor_name: Optional[str] = None):
    """Liste les rendez-vous filtrés par client ou médecin."""
    db = SessionLocal()
    try:
        query = db.query(RendezVousDB)
        
        if client_name:
            query = query.filter(RendezVousDB.client_name == client_name)
        elif doctor_name:
            query = query.filter(RendezVousDB.doctor_name == doctor_name)
        
        rendez_vous = query.all()
        
        if not rendez_vous:
            filter_info = f" pour {client_name}" if client_name else f" pour Dr. {doctor_name}" if doctor_name else ""
            return {
                "rendez_vous": [], 
                "message": f"Aucun rendez-vous trouvé{filter_info}."
            }
        
        liste = [
            {
                "id": rdv.id,
                "client_name": rdv.client_name,
                "doctor_name": rdv.doctor_name,
                "date_time": rdv.date_time,
                "service": rdv.service,
            }
            for rdv in rendez_vous
        ]
        return {"rendez_vous": liste, "count": len(liste)}
    finally:
        db.close()

def verifier_disponibilite_journee(date: str):
    """
    Vérifie les disponibilités pour une journée entière.
    
    Args:
        date (str): La date cible au format 'YYYY-MM-DD'.
    """
    db = SessionLocal()
    try:
        rendez_vous_jour = (
            db.query(RendezVousDB)
            .filter(RendezVousDB.date_time.like(f"{date}%"))
            .all()
        )
        
        if not rendez_vous_jour:
            return {
                "status": "success",
                "message": f"Toute la journée du {date} est entièrement libre. Tu peux proposer n'importe quelle heure.",
                "disponibilites": [],
                "occupees": []
            }
        
        heures_occupees = sorted([rdv.date_time.split(" ")[1] for rdv in rendez_vous_jour])
        
        # Extraire les créneaux libres (simplifié : 8h-18h par défaut)
        toutes_heures = [f"{h:02d}:00" for h in range(8, 18)]
        heures_libres = [h for h in toutes_heures if h not in heures_occupees]
        
        return {
            "status": "success",
            "message": f"Créneaux disponibles le {date}: {', '.join(heures_libres) if heures_libres else 'Aucun créneau libre'}. Créneaux occupés: {', '.join(heures_occupees)}",
            "disponibilites": heures_libres,
            "occupees": heures_occupees
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def lister_tous_rendez_vous():
    """Liste tous les rendez-vous (réservé aux médecins)."""
    db = SessionLocal()
    try:
        rendez_vous = db.query(RendezVousDB).all()
        
        liste = [
            {
                "id": rdv.id,
                "client_name": rdv.client_name,
                "doctor_name": rdv.doctor_name,
                "date_time": rdv.date_time,
                "service": rdv.service,
            }
            for rdv in rendez_vous
        ]
        return {"rendez_vous": liste, "count": len(liste)}
    finally:
        db.close()


def lister_patients():
    """Liste tous les patients (réservé aux médecins)."""
    db = SessionLocal()
    try:
        patients = db.query(UserDB).filter(UserDB.role == "patient").all()
        return {
            "patients": [
                {"username": p.username, "full_name": p.full_name}
                for p in patients
            ]
        }
    finally:
        db.close()


def lister_medecins():
    """Liste tous les médecins."""
    db = SessionLocal()
    try:
        medecins = db.query(UserDB).filter(UserDB.role == "medecin").all()
        return {
            "medecins": [
                {"username": m.username, "full_name": m.full_name}
                for m in medecins
            ]
        }
    finally:
        db.close()

    
available_tools = {
    "prendre_rendez_vous": prendre_rendez_vous,
    "verifier_creneau_disponible": verifier_creneau_disponible,
    "verifier_disponibilite_journee": verifier_disponibilite_journee,
    "annuler_rendez_vous": annuler_rendez_vous,
    "lister_rendez_vous": lister_rendez_vous,
    "lister_tous_rendez_vous": lister_tous_rendez_vous,
    "lister_patients": lister_patients,
    "lister_medecins": lister_medecins,
}