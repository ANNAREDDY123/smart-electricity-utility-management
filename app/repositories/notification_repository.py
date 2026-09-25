from datetime import datetime

from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationStatus,
)
from app.schemas.notification import NotificationCreate


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        data: NotificationCreate,
    ) -> Notification:

        notification = Notification(
            user_id=data.user_id,
            notification_type=data.notification_type,
            title=data.title,
            message=data.message,
            status=NotificationStatus.PENDING,
        )

        self.db.add(notification)
        self.db.flush()

        return notification

    def get_by_id(
        self,
        notification_id: int,
    ) -> Notification | None:

        return self.db.get(
            Notification,
            notification_id,
        )

    def list_notifications(
        self,
        *,
        user_id: int | None = None,
        status: NotificationStatus | None = None,
    ) -> list[Notification]:

        query = self.db.query(Notification)

        if user_id is not None:
            query = query.filter(
                Notification.user_id == user_id
            )

        if status is not None:
            query = query.filter(
                Notification.status == status
            )

        return (
            query
            .order_by(Notification.created_at.desc())
            .all()
        )

    def mark_sent(
        self,
        notification: Notification,
    ) -> Notification:

        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.utcnow()

        self.db.add(notification)
        self.db.flush()

        return notification

    def mark_failed(
        self,
        notification: Notification,
    ) -> Notification:

        notification.status = NotificationStatus.FAILED

        self.db.add(notification)
        self.db.flush()

        return notification