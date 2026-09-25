from datetime import date
from decimal import Decimal
from enum import Enum

from sqlalchemy import Date, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MeterStatus(str, Enum):
    ACTIVE = "Active"
    FAULTY = "Faulty"
    REMOVED = "Removed"


class Meter(Base):
    __tablename__ = "meters"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    connection_id: Mapped[int] = mapped_column(
        ForeignKey("connections.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    meter_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    meter_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    installation_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    initial_reading: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    current_reading: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    meter_status: Mapped[MeterStatus] = mapped_column(
        SQLEnum(MeterStatus),
        nullable=False,
        default=MeterStatus.ACTIVE,
        index=True,
    )