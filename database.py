from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import hashlib

SQLALCHEMY_DATABASE_URL = "sqlite:///./rendez_vous.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)  # SHA256 hash
    role = Column(String, default="patient")  # "patient" ou "medecin"
    full_name = Column(String)

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash a password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def verify_password(cls, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return cls.hash_password(password) == password_hash


class RendezVousDB(Base):
    __tablename__ = "rendez_vous"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, index=True)
    doctor_name = Column(String, index=True, nullable=True)  # Ajout du médecin
    date_time = Column(String)
    service = Column(String)


# Create all tables
Base.metadata.create_all(bind=engine)

# Utilitaire pour créer un utilisateur admin par défaut si non existant
def init_default_users():
    db = SessionLocal()
    try:
        # Vérifier si des utilisateurs existent déjà
        if db.query(UserDB).count() == 0:
            # Créer un médecin par défaut
            medecin = UserDB(
                username="dr.yohan",
                password_hash=UserDB.hash_password("password123"),
                role="medecin",
                full_name="Dr. Yohan"
            )
            db.add(medecin)
            
            # Créer un patient par défaut
            patient = UserDB(
                username="lewis",
                password_hash=UserDB.hash_password("password123"),
                role="patient",
                full_name="Lewis Hamilton"
            )
            db.add(patient)
            
            db.commit()
            print("Utilisateurs par défaut créés")
    finally:
        db.close()

# Initialiser les utilisateurs par défaut au démarrage
init_default_users()