from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NotificationType(str, Enum):
    BILL_GENERATED = "Bill Generated"
    BILL_DUE_REMINDER = "Bill Due Reminder"
    PAYMENT_SUCCESS = "Payment Success"
    PAYMENT_FAILURE = "Payment Failure"
    BILL_OVERDUE = "Bill Overdue"
    COMPLAINT_ASSIGNED = "Complaint Assigned"
    COMPLAINT_RESOLVED = "Complaint Resolved"
    SERVICE_REQUEST_APPROVED = "Service Request Approved"
    METER_REPLACEMENT_COMPLETED = "Meter Replacement Completed"


class NotificationStatus(str, Enum):
    PENDING = "Pending"
    SENT = "Sent"
    FAILED = "Failed"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[NotificationStatus] = mapped_column(
        SQLEnum(NotificationStatus),
        nullable=False,
        default=NotificationStatus.PENDING,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )