from database import RendezVousDB, SessionLocal


def prendre_rendez_vous(client_name: str, date_time: str, service: str):
    """Réserve un nouveau rendez-vous dans le système."""
    db = SessionLocal()
    nouveau_rdv = RendezVousDB(
        client_name=client_name, date_time=date_time, service=service
    )
    db.add(nouveau_rdv)
    db.commit()
    db.close()
    return {
        "status": "success",
        "message": f"Rendez-vous bien enregistré pour {client_name} le {date_time}.",
    }


def verifier_disponibilite(date_time: str):
    """Vérifie si un créneau horaire est libre."""
    db = SessionLocal()
    existant = (
        db.query(RendezVousDB).filter(RendezVousDB.date_time == date_time).first()
    )
    db.close()
    if existant:
        return {"disponible": False, "message": "Ce créneau est déjà pris."}
    return {"disponible": True, "message": "Le créneau est libre."}

def annuler_rendez_vous(client_name: str, date_time: str):
    """Annule un rendez-vous existant en fonction du nom du client et de la date."""
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

def lister_rendez_vous():
    """Liste tous les rendez-vous enregistrés dans le système."""
    db = SessionLocal()
    try:
        rendez_vous = db.query(RendezVousDB).all()
        if not rendez_vous:
            return {"rendez_vous": [], "message": "Aucun rendez-vous enregistré pour le moment."}
        
        liste = [
            {
                "id": rdv.id,
                "client_name": rdv.client_name,
                "date_time": rdv.date_time,
                "service": rdv.service,
            }
            for rdv in rendez_vous
        ]
        return {"rendez_vous": liste}
    finally:
        db.close()

available_tools = {
    "prendre_rendez_vous": prendre_rendez_vous,
    "verifier_disponibilite": verifier_disponibilite,
}