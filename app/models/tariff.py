from datetime import date
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Date,
    Enum as SQLEnum,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TariffStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class Tariff(Base):
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    tariff_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    connection_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    minimum_units: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    maximum_units: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    rate_per_unit: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        nullable=False,
    )

    fixed_charge: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    status: Mapped[TariffStatus] = mapped_column(
        SQLEnum(TariffStatus),
        nullable=False,
        default=TariffStatus.ACTIVE,
        index=True,
    )