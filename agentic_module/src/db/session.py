from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core import settings

# Create Engine (connection to Neon DB)
engine = create_engine(settings.DATABASE_URL, echo=False)

# Create Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# Dependency (get_db) to be used in FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()