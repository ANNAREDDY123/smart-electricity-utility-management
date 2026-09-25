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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BillStatus(str, Enum):
    GENERATED = "Generated"
    PENDING = "Pending"
    PAID = "Paid"
    OVERDUE = "Overdue"
    CANCELLED = "Cancelled"


class Bill(Base):
    __tablename__ = "bills"

    __table_args__ = (
        UniqueConstraint(
            "connection_id",
            "billing_month",
            name="uq_bill_connection_billing_month",
        ),
    )

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

    billing_month: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        index=True,
    )

    units_consumed: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    energy_charge: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    fixed_charge: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    tax: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    late_fee: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    discount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    bill_status: Mapped[BillStatus] = mapped_column(
        SQLEnum(BillStatus),
        nullable=False,
        default=BillStatus.GENERATED,
        index=True,
    )