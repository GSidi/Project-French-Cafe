from app.database import SessionLocal
from app.models import Venue, Table, TableStatus
from sqlalchemy import text

db = SessionLocal()


try:
    db.execute(text("TRUNCATE venues RESTART IDENTITY CASCADE"))
    VENUES = [
        {
            "name": "Bricks",
            "address": "Test Address 13",
            "tables": [
                {
                    "label": "T1", "seats": 2, "pos_x": 0, "pos_y": 0, "status": TableStatus.OCCUPIED
                },
                {
                    "label": "T2", "seats": 4, "pos_x": 0, "pos_y": 1, "status": TableStatus.FREE
                },
                {
                    "label": "T3", "seats": 6, "pos_x": 1, "pos_y": 0, "status": TableStatus.FREE
                },
                {
                    "label": "T4", "seats": 5, "pos_x": 1, "pos_y": 1, "status": TableStatus.OCCUPIED
                },
                {
                    "label": "T5", "seats": 3, "pos_x": 0, "pos_y": 2, "status": TableStatus.FREE, "is_active": False
                },
                {
                    "label": "T6", "seats": 7, "pos_x": 2, "pos_y": 0, "status": TableStatus.OCCUPIED
                }

            ]
        },
        {
            "name": "Grasshopper",
            "address": "Test Address 136",
            "tables": [
                {
                    "label": "T1", "seats": 2, "pos_x": 1, "pos_y": 1, "status": TableStatus.FREE
                },
                {
                    "label": "T2", "seats": 3, "pos_x": 1, "pos_y": 2, "status": TableStatus.FREE
                },
                {
                    "label": "T3", "seats": 4, "pos_x": 2, "pos_y": 1, "status": TableStatus.FREE
                },
                {
                    "label": "T4", "seats": 5, "pos_x": 2, "pos_y": 2, "status": TableStatus.FREE
                },
                {
                    "label": "T5", "seats": 6, "pos_x": 3, "pos_y": 1, "status": TableStatus.FREE
                },
                {
                    "label": "T6", "seats": 7, "pos_x": 1, "pos_y": 3, "status": TableStatus.FREE
                }

            ]
        },
        {
            "name": "Maya",
            "address": "Test Address 700",
            "tables": [
                {
                    "label": "T1", "seats": 2, "pos_x": 0, "pos_y": 0, "status": TableStatus.OCCUPIED
                },
                {
                    "label": "T2", "seats": 3, "pos_x": 0, "pos_y": 1, "status": TableStatus.FREE
                },
                {
                    "label": "T3", "seats": 4, "pos_x": 0, "pos_y": 2, "status": TableStatus.OCCUPIED
                },
                {
                    "label": "T4", "seats": 5, "pos_x": 0, "pos_y": 3, "status": TableStatus.FREE
                },
                {
                    "label": "T5", "seats": 6, "pos_x": 1, "pos_y": 0, "status": TableStatus.FREE
                },
                {
                    "label": "T6", "seats": 7, "pos_x": 2, "pos_y": 0, "status": TableStatus.OCCUPIED
                }

            ]
        },
        {
            "name": "Buddies",
            "address": "Test Address 800",
            "tables": []
        }
    ]

    for venue in VENUES:
            venue_obj = Venue(name=venue["name"], address=venue["address"])
            db.add(venue_obj)
            db.flush()

            for table in venue["tables"]:
                db.add(Table(
                    venue_id=venue_obj.id,
                    **table
                ))

    db.commit()
finally:
    db.close()
