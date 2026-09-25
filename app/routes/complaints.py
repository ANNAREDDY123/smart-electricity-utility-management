from math import ceil

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.complaint import (
    ComplaintPriority,
    ComplaintStatus,
    ComplaintType,
)
from app.models.notification import NotificationType
from app.schemas.complaint import (
    ComplaintAssign,
    ComplaintCreate,
    ComplaintDetailResponse,
    ComplaintHistoryResponse,
    ComplaintPaginationResponse,
    ComplaintResponse,
    ComplaintStatusUpdate,
)
from app.services.complaint_service import ComplaintService
from app.services.notification_service import NotificationService
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"],
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
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_complaint(
    data: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):
    service = ComplaintService(db)

    complaint = service.create_complaint(
        data=data,
        current_user=current_user,
    )

    db.commit()
    db.refresh(complaint)

    return complaint


@router.get(
    "",
    response_model=ComplaintPaginationResponse[ComplaintResponse]
    | list[ComplaintResponse],
)
def get_complaints(
    customer_id: int | None = Query(
        default=None,
        gt=0,
    ),
    connection_id: int | None = Query(
        default=None,
        gt=0,
    ),
    complaint_type: ComplaintType | None = Query(
        default=None,
    ),
    priority: ComplaintPriority | None = Query(
        default=None,
    ),
    complaint_status: ComplaintStatus | None = Query(
        default=None,
    ),
    assigned_to: int | None = Query(
        default=None,
        gt=0,
    ),
    page: int | None = Query(
        default=None,
        ge=1,
    ),
    limit: int | None = Query(
        default=None,
        ge=1,
        le=100,
    ),
    sort_by: str | None = Query(
        default=None,
    ),
    sort_order: str | None = Query(
        default=None,
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):
    service = ComplaintService(db)

    # Preserve the original Level 9 behavior:
    # when pagination/sorting parameters are not supplied,
    # return a plain list.
    if (
        customer_id is None
        and connection_id is None
        and complaint_type is None
        and priority is None
        and complaint_status is None
        and assigned_to is None
        and page is None
        and limit is None
        and sort_by is None
        and sort_order is None
    ):
        complaints, _ = service.list_complaints(
            customer_id=customer_id,
            connection_id=connection_id,
            complaint_type=complaint_type,
            priority=priority,
            complaint_status=complaint_status,
            assigned_to=assigned_to,
            page=1,
            limit=100,
            sort_by="created_at",
            sort_order="desc",
        )

        return complaints

    # Level 13 paginated behavior
    page = page or 1
    limit = limit or 20
    sort_by = sort_by or "created_at"
    sort_order = sort_order or "desc"

    complaints, total = service.list_complaints(
        customer_id=customer_id,
        connection_id=connection_id,
        complaint_type=complaint_type,
        priority=priority,
        complaint_status=complaint_status,
        assigned_to=assigned_to,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    pages = ceil(total / limit) if total else 0

    return {
        "items": complaints,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get(
    "/{complaint_id}",
    response_model=ComplaintDetailResponse,
)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):
    service = ComplaintService(db)

    complaint = service.get_complaint(
        complaint_id
    )

    history = service.get_history(
        complaint_id
    )

    return {
        "id": complaint.id,
        "customer_id": complaint.customer_id,
        "connection_id": complaint.connection_id,
        "complaint_type": complaint.complaint_type,
        "description": complaint.description,
        "priority": complaint.priority,
        "assigned_to": complaint.assigned_to,
        "status": complaint.status,
        "created_at": complaint.created_at,
        "updated_at": complaint.updated_at,
        "history": history,
    }


@router.put(
    "/{complaint_id}/assign",
    response_model=ComplaintResponse,
)
def assign_complaint(
    complaint_id: int,
    data: ComplaintAssign,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Customer Service Agent",
            "Billing Officer",
        )
    ),
):
    service = ComplaintService(db)

    complaint = service.assign_complaint(
        complaint_id=complaint_id,
        data=data,
        current_user=current_user,
    )

    db.commit()
    db.refresh(complaint)

    # Complaint Assigned Notification
    if complaint.assigned_to is not None:
        notification_service = NotificationService(db)

        notification_service.create_event_notification(
            user_id=complaint.assigned_to,
            notification_type=NotificationType.COMPLAINT_ASSIGNED,
            title="Complaint Assigned",
            message=(
                f"Complaint {complaint.id} has been assigned to you. "
                f"Priority: {complaint.priority}. "
                f"Type: {complaint.complaint_type}."
            ),
            background_tasks=background_tasks,
        )

    return complaint


@router.put(
    "/{complaint_id}/status",
    response_model=ComplaintResponse,
)
def update_complaint_status(
    complaint_id: int,
    data: ComplaintStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Field Technician",
            "Customer Service Agent",
        )
    ),
):
    service = ComplaintService(db)

    complaint = service.update_status(
        complaint_id=complaint_id,
        data=data,
        current_user=current_user,
    )

    db.commit()
    db.refresh(complaint)

    # Complaint Resolved Notification
    if (
        complaint.status == ComplaintStatus.RESOLVED
        and complaint.assigned_to is not None
    ):
        notification_service = NotificationService(db)

        notification_service.create_event_notification(
            user_id=complaint.assigned_to,
            notification_type=NotificationType.COMPLAINT_RESOLVED,
            title="Complaint Resolved",
            message=(
                f"Complaint {complaint.id} has been resolved successfully. "
                f"Complaint type: {complaint.complaint_type}. "
                f"Priority: {complaint.priority}."
            ),
            background_tasks=background_tasks,
        )

    return complaint