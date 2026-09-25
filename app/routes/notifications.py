from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notification import NotificationStatus
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
)
from app.services.notification_service import (
    NotificationService,
)
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


allowed_roles = (
    "Super Admin",
    "Billing Officer",
    "Field Technician",
    "Customer Service Agent",
    "Customer",
)


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_notification(
    data: NotificationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):

    service = NotificationService(db)

    return service.create_and_schedule_notification(
        data=data,
        background_tasks=background_tasks,
    )


@router.get(
    "",
    response_model=list[NotificationResponse],
)
def list_notifications(
    notification_status: NotificationStatus | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):

    service = NotificationService(db)

    return service.list_notifications(
        user_id=current_user.id,
        notification_status=notification_status,
    )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):

    service = NotificationService(db)

    notification = service.get_notification(
        notification_id
    )

    # Users can see their own notifications.
    # Administrative roles can see notifications
    # for other users as well.

    admin_roles = (
        "Super Admin",
        "Billing Officer",
        "Customer Service Agent",
    )

    if (
        current_user.role not in admin_roles
        and notification.user_id != current_user.id
    ):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own notifications",
        )

    return notification