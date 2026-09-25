from datetime import date
from enum import Enum

from sqlalchemy import Date, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ServiceRequestType(str, Enum):
    NEW_CONNECTION = "New Connection"
    LOAD_CHANGE = "Load Change"
    METER_REPLACEMENT = "Meter Replacement"
    NAME_CHANGE = "Name Change"
    ADDRESS_CHANGE = "Address Change"
    DISCONNECTION = "Disconnection"
    RECONNECTION = "Reconnection"


class ServiceRequestStatus(str, Enum):
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    COMPLETED = "Completed"


class ServiceRequest(Base):
    __tablename__ = "service_requests"

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

    connection_id: Mapped[int | None] = mapped_column(
        ForeignKey("connections.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    request_type: Mapped[ServiceRequestType] = mapped_column(
        SQLEnum(ServiceRequestType),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    requested_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    status: Mapped[ServiceRequestStatus] = mapped_column(
        SQLEnum(ServiceRequestStatus),
        nullable=False,
        default=ServiceRequestStatus.SUBMITTED,
        index=True,
    )