from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PaymentMethod(str, Enum):
    UPI = "UPI"
    CARD = "Card"
    NET_BANKING = "Net Banking"
    WALLET = "Wallet"


class PaymentStatus(str, Enum):
    PENDING = "Pending"
    SUCCESS = "Success"
    FAILED = "Failed"
    REFUNDED = "Refunded"


class Payment(Base):
    __tablename__ = "payments"

    __table_args__ = (
        UniqueConstraint(
            "transaction_id",
            name="uq_payments_transaction_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    bill_id: Mapped[int] = mapped_column(
        ForeignKey("bills.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    payment_method: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(PaymentMethod),
        nullable=False,
    )

    transaction_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    payment_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    payment_status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
    )