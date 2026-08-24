"""SQLAlchemy engine, session factory, and get_db dependency."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from collections.abc import Iterator

engine = create_engine(settings.database_url, pool_pre_ping=True, echo=True)


#Naming note: SessionLocal is CapWords deliberately, even though it's a variable, not a class. It's a factory that produces objects,
#so you call it like a constructor — db = SessionLocal(). The convention comes straight from the FastAPI docs and signals "this is callable, and calling it makes a thing."

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        