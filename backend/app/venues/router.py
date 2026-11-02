"""Venues: HTTP endpoints (APIRouter). Knows HTTP, not SQL."""
from app.database import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.venues.service import list_venues
from app.venues.schemas import VenueSummary

router = APIRouter(prefix="/venues", tags=["venues"])

@router.get("", response_model=list[VenueSummary])
def get_venues(db: Session = Depends(get_db)):
    return list_venues(db=db)
