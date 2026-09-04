"""All SQLAlchemy ORM models (see DATA_MODEL.md)."""
from app.base import Base
from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, String, Identity, Text, Boolean, func, \
    SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from enum import StrEnum
from sqlalchemy import  Enum as SQLEnum


class Venue(Base):
    __tablename__ = "venues"
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text())
    address: Mapped[str | None] = mapped_column(Text())
    timezone: Mapped[str] = mapped_column(Text(), server_default="UTC")
    is_active: Mapped[bool] = mapped_column(server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class UserRole(StrEnum):
    ADMIN = "ADMIN"
    STAFF = "STAFF"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    email: Mapped[str] = mapped_column(Text(),unique=True)
    hashed_password: Mapped[str] = mapped_column(Text())
    name: Mapped[str | None] = mapped_column(Text())
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole, name="user_role"))
    is_active: Mapped[bool] = mapped_column(server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TableStatus(StrEnum):
    FREE = "FREE"
    OCCUPIED = "OCCUPIED"


class Table(Base):
    __tablename__ = "tables"
    __table_args__ = (
        UniqueConstraint("venue_id", "label", name="uniq_tables_venue_label"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"))
    label: Mapped[str] = mapped_column(Text())
    seats: Mapped[int] = mapped_column(SmallInteger(), server_default="2")
    is_active: Mapped[bool] = mapped_column(server_default="true")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    pos_x: Mapped[int] = mapped_column(Integer(), server_default="0")
    pos_y: Mapped[int] = mapped_column(Integer(), server_default="0")
    status: Mapped[TableStatus] = mapped_column(SQLEnum(TableStatus, name="table_status"), server_default="FREE")
