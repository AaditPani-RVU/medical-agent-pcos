import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Check .env for a Postgres connection string, else fallback to SQLite
DB_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///d:/Medical Agent/MedicalAgent/pocs/womens_health_pcos/data/pcos_knowledge.db"
)

# SQLite needs check_same_thread=False
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}

engine = create_engine(DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from pocs.womens_health_pcos.database.base import Base
    import pocs.womens_health_pcos.database.models  # Register models
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
