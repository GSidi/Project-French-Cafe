"""All SQLAlchemy ORM models (see DATA_MODEL.md)."""
from app.base import Base
from sqlalchemy import BigInteger,  DateTime,  ForeignKey, Integer,  Identity, Text,  func, \
    SmallInteger, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from enum import StrEnum
from sqlalchemy import Enum as SQLEnum


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

user_role_enum = SQLEnum(UserRole, name="user_role")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    email: Mapped[str] = mapped_column(Text(), unique=True)
    hashed_password: Mapped[str] = mapped_column(Text())
    name: Mapped[str | None] = mapped_column(Text())
    role: Mapped[UserRole] = mapped_column(user_role_enum)
    is_active: Mapped[bool] = mapped_column(server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TableStatus(StrEnum):
    FREE = "FREE"
    OCCUPIED = "OCCUPIED"

table_status_enum = SQLEnum(TableStatus, name="table_status")

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
    status: Mapped[TableStatus] = mapped_column(table_status_enum, server_default="FREE")


class StatusSource(StrEnum):
    STAFF_MANUAL = "STAFF_MANUAL"
    SYSTEM = "SYSTEM"

class StatusEvent(Base):
    __tablename__ = "status_events"
    __table_args__ = (
        Index("idx_status_events_table_time", "table_id", "created_at"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("tables.id"))
    old_status: Mapped[TableStatus | None] = mapped_column(table_status_enum)
    new_status: Mapped[TableStatus] = mapped_column(table_status_enum)
    source: Mapped[StatusSource] = mapped_column(SQLEnum(StatusSource, name="status_source"))
    changed_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


