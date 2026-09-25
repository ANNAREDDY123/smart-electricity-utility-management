from enum import Enum

from sqlalchemy import Enum as SQLEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TechnicianAvailability(str, Enum):
    AVAILABLE = "Available"
    BUSY = "Busy"
    UNAVAILABLE = "Unavailable"


class Technician(Base):
    __tablename__ = "technicians"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    employee_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    specialization: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    availability_status: Mapped[TechnicianAvailability] = mapped_column(
        SQLEnum(TechnicianAvailability),
        nullable=False,
        default=TechnicianAvailability.AVAILABLE,
        index=True,
    )