from datetime import date
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Date,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReadingSource(str, Enum):
    MANUAL = "Manual"
    SMART_METER = "Smart Meter"
    FIELD_TECHNICIAN = "Field Technician"


class MeterReading(Base):
    __tablename__ = "meter_readings"

    __table_args__ = (
        UniqueConstraint(
            "meter_id",
            "billing_period",
            name="uq_meter_reading_billing_period",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    meter_id: Mapped[int] = mapped_column(
        ForeignKey("meters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    reading_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    previous_reading: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    current_reading: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    units_consumed: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    reading_source: Mapped[ReadingSource] = mapped_column(
        SQLEnum(ReadingSource),
        nullable=False,
        index=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Format: YYYY-MM
    # Example: 2026-09
    billing_period: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        index=True,
    )