"""FastAPI app factory; mounts each module router."""
from app.database import get_db
from fastapi import FastAPI,Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings

app = FastAPI(title="French cafe ala Grecia")



@app.get("/health")
def health(db: Session = Depends(get_db)):
    response = db.execute(text("SELECT 1")).scalar()
    return {"status": "ok", "db": settings.postgres_db, "check": response}
