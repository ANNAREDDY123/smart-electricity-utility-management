from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.notification import (
    NotificationStatus,
    NotificationType,
)


class NotificationCreate(BaseModel):
    user_id: int | None = None
    notification_type: NotificationType
    title: str
    message: str


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    notification_type: NotificationType
    title: str
    message: str
    status: NotificationStatus
    created_at: datetime
    sent_at: datetime | None