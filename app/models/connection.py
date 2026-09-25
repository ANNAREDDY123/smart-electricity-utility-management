from datetime import date
from decimal import Decimal
from enum import Enum

from sqlalchemy import Date, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConnectionType(str, Enum):
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"
    INDUSTRIAL = "Industrial"


class ConnectionStatus(str, Enum):
    ACTIVE = "Active"
    DISCONNECTED = "Disconnected"
    SUSPENDED = "Suspended"


class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    connection_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    connection_type: Mapped[ConnectionType] = mapped_column(
        SQLEnum(ConnectionType),
        nullable=False,
        index=True,
    )

    sanctioned_load: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    tariff_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    connection_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[ConnectionStatus] = mapped_column(
        SQLEnum(ConnectionStatus),
        nullable=False,
        default=ConnectionStatus.ACTIVE,
        index=True,
    )