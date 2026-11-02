"""FastAPI app factory; mounts each module router."""
from app.database import get_db
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings
from app.venues.router import router as venue_router

app = FastAPI(title="French cafe ala Grecia")
app.include_router(venue_router)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    response = db.execute(text("SELECT 1")).scalar()
    return {"status": "ok", "db": settings.postgres_db, "check": response}
