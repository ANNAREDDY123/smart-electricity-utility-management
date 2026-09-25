from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ComplaintType(str, Enum):
    POWER_FAILURE = "Power Failure"
    VOLTAGE_ISSUE = "Voltage Issue"
    METER_ISSUE = "Meter Issue"
    BILLING_ISSUE = "Billing Issue"
    CONNECTION_ISSUE = "Connection Issue"
    OTHER = "Other"


class ComplaintPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    EMERGENCY = "Emergency"


class ComplaintStatus(str, Enum):
    OPEN = "Open"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class Complaint(Base):
    __tablename__ = "complaints"

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

    connection_id: Mapped[int] = mapped_column(
        ForeignKey("connections.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    complaint_type: Mapped[ComplaintType] = mapped_column(
        SQLEnum(ComplaintType),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    priority: Mapped[ComplaintPriority] = mapped_column(
        SQLEnum(ComplaintPriority),
        nullable=False,
        default=ComplaintPriority.MEDIUM,
        index=True,
    )

    assigned_to: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[ComplaintStatus] = mapped_column(
        SQLEnum(ComplaintStatus),
        nullable=False,
        default=ComplaintStatus.OPEN,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )


class ComplaintHistory(Base):
    __tablename__ = "complaint_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    old_status: Mapped[ComplaintStatus | None] = mapped_column(
        SQLEnum(ComplaintStatus),
        nullable=True,
    )

    new_status: Mapped[ComplaintStatus] = mapped_column(
        SQLEnum(ComplaintStatus),
        nullable=False,
    )

    changed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )