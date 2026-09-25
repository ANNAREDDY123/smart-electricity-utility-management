from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationStatus,
    NotificationType,
)
from app.repositories.notification_repository import (
    NotificationRepository,
)
from app.schemas.notification import (
    NotificationCreate,
)


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = NotificationRepository(db)

    def create_notification(
        self,
        data: NotificationCreate,
    ) -> Notification:

        return self.repository.create(data)

    def get_notification(
        self,
        notification_id: int,
    ) -> Notification:

        notification = self.repository.get_by_id(
            notification_id
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        return notification

    def list_notifications(
        self,
        *,
        user_id: int | None = None,
        notification_status: NotificationStatus | None = None,
    ) -> list[Notification]:

        return self.repository.list_notifications(
            user_id=user_id,
            status=notification_status,
        )

    def send_notification(
        self,
        notification_id: int,
    ) -> None:

        notification = self.repository.get_by_id(
            notification_id
        )

        if not notification:
            return

        try:
            # This is the notification delivery layer.
            # Email/SMS integration can be added later.
            #
            # For the current assignment implementation,
            # creating the notification and marking it SENT
            # represents successful background processing.

            self.repository.mark_sent(
                notification
            )

            self.db.commit()

        except Exception:
            self.db.rollback()

            notification = self.repository.get_by_id(
                notification_id
            )

            if notification:
                self.repository.mark_failed(
                    notification
                )
                self.db.commit()

    def create_and_schedule_notification(
        self,
        data: NotificationCreate,
        background_tasks: BackgroundTasks,
    ) -> Notification:

        notification = self.repository.create(data)

        self.db.commit()
        self.db.refresh(notification)

        background_tasks.add_task(
            self._process_notification,
            notification.id,
        )

        return notification

    def _process_notification(
        self,
        notification_id: int,
    ) -> None:

        # BackgroundTasks executes this after the
        # HTTP response is prepared.
        #
        # A new database session is intentionally created
        # for background processing so that the request
        # session is not reused after the request finishes.

        from app.database import SessionLocal

        db = SessionLocal()

        try:
            service = NotificationService(db)

            service.send_notification(
                notification_id
            )

        finally:
            db.close()

    def create_event_notification(
        self,
        *,
        user_id: int | None,
        notification_type: NotificationType,
        title: str,
        message: str,
        background_tasks: BackgroundTasks,
    ) -> Notification:

        data = NotificationCreate(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
        )

        return self.create_and_schedule_notification(
            data=data,
            background_tasks=background_tasks,
        )