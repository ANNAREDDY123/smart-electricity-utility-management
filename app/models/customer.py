from enum import Enum

from sqlalchemy import Boolean, Enum as SQLEnum
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CustomerStatus(str, Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    CLOSED = "Closed"


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    customer_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    address: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )

    status: Mapped[CustomerStatus] = mapped_column(
        SQLEnum(CustomerStatus),
        nullable=False,
        default=CustomerStatus.ACTIVE,
        index=True,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )