"""All SQLAlchemy ORM models (see DATA_MODEL.md)."""
from app.base import Base
from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, String, Identity, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class Venue(Base):
    __tablename__ = "venues"
    id: Mapped[int] = mapped_column(BigInteger,Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text())
    address: Mapped[str | None] = mapped_column(Text())
    timezone: Mapped[str] = mapped_column(Text(), server_default="UTC")
    is_active: Mapped[bool] = mapped_column(server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())




