"""Venues: Business logic and DB queries. Knows SQL, not HTTP."""
from app.models import Venue, Table, TableStatus
from app.venues.schemas import VenueSummary
from sqlalchemy import select, func
from sqlalchemy.orm import Session


def list_venues(db: Session) -> list[VenueSummary]:
    """Brings all the active venues"""
    list_of_venues = []
    venues = db.scalars(select(Venue).where(Venue.is_active == True)).all()

    for venue in venues:
        name = venue.name
        #db.execute.scala_one means there must be exactly one vlue , just ot avoid the any | none type error
        total_tables = db.execute(select(func.count()).select_from(Table).where(Table.venue_id == venue.id,
                                                                               Table.is_active == True)).scalar_one()
        free_tables = db.execute(select(func.count()).select_from(Table).where(Table.venue_id == venue.id,
                                                                              Table.status == TableStatus.FREE,
                                                                              Table.is_active == True)).scalar_one()

        list_of_venues.append(VenueSummary(id=venue.id, name=name, total_tables=total_tables, free_tables=free_tables,
                                         address=venue.address))

    return list_of_venues
