from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.service_request import (
    ServiceRequestStatus,
    ServiceRequestType,
)
from app.models.notification import NotificationType
from app.services.notification_service import NotificationService
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
    status,
)


from app.schemas.service_request import (
    ServiceRequestCreate,
    ServiceRequestResponse,
)
from app.services.service_request_service import (
    ServiceRequestService,
)
from app.utils.dependencies import (
    get_current_active_user,
    require_roles,
)


router = APIRouter(
    prefix="/service-requests",
    tags=["Service Requests"],
)


@router.post(
    "",
    response_model=ServiceRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service_request(
    data: ServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = ServiceRequestService(db)

    service_request = service.create_request(data)

    db.commit()
    db.refresh(service_request)

    return service_request


@router.get(
    "",
    response_model=list[ServiceRequestResponse],
)
def get_service_requests(
    customer_id: int | None = Query(
        default=None,
        gt=0,
    ),
    connection_id: int | None = Query(
        default=None,
        gt=0,
    ),
    request_type: ServiceRequestType | None = Query(
        default=None,
    ),
    request_status: ServiceRequestStatus | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = ServiceRequestService(db)

    return service.list_requests(
        customer_id=customer_id,
        connection_id=connection_id,
        request_type=request_type,
        request_status=request_status,
    )


@router.get(
    "/{service_request_id}",
    response_model=ServiceRequestResponse,
)
def get_service_request(
    service_request_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = ServiceRequestService(db)

    return service.get_request(
        service_request_id
    )


@router.put(
    "/{service_request_id}/approve",
    response_model=ServiceRequestResponse,
)
def approve_service_request(
    service_request_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Customer Service Agent",
        )
    ),
):
    service = ServiceRequestService(db)

    service_request = service.approve_request(
        service_request_id
    )

    db.commit()
    db.refresh(service_request)

    # Service Request Approved Notification
    notification_service = NotificationService(db)

    notification_service.create_event_notification(
        user_id=current_user.id,
        notification_type=NotificationType.SERVICE_REQUEST_APPROVED,
        title="Service Request Approved",
        message=(
            f"Service request {service_request.id} has been approved. "
            f"Request type: {service_request.request_type}. "
            f"Requested date: {service_request.requested_date}."
        ),
        background_tasks=background_tasks,
    )

    return service_request


@router.put(
    "/{service_request_id}/reject",
    response_model=ServiceRequestResponse,
)
def reject_service_request(
    service_request_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Customer Service Agent",
        )
    ),
):
    service = ServiceRequestService(db)

    service_request = service.reject_request(
        service_request_id
    )

    db.commit()
    db.refresh(service_request)

    return service_request


@router.put(
    "/{service_request_id}/complete",
    response_model=ServiceRequestResponse,
)
def complete_service_request(
    service_request_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Customer Service Agent",
            "Field Technician",
        )
    ),
):
    service = ServiceRequestService(db)

    service_request = service.complete_request(
        service_request_id
    )

    db.commit()
    db.refresh(service_request)

    return service_request