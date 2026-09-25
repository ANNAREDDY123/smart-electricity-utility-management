from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
    status,
)

from app.models.notification import NotificationType
from app.services.notification_service import NotificationService
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.meter import (
    MeterCreate,
    MeterPaginationResponse,
    MeterReplace,
    MeterResponse,
    MeterUpdate,
)
from app.services.meter_service import MeterService
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/meters",
    tags=["Smart Meters"],
)


# ============================================================
# CREATE METER
# ============================================================

@router.post(
    "",
    response_model=MeterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_meter(
    data: MeterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.FIELD_TECHNICIAN,
        )
    ),
):
    service = MeterService(db)

    meter = service.create_meter(data)

    db.commit()
    db.refresh(meter)

    return meter


# ============================================================
# LIST METERS
# ============================================================

@router.get(
    "",
    response_model=MeterPaginationResponse,
)
def list_meters(
    connection_id: int | None = Query(default=None, gt=0),
    meter_type: str | None = None,
    meter_status: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sort_by: str = Query(default="id"),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.FIELD_TECHNICIAN,
            UserRole.BILLING_OFFICER,
            UserRole.CUSTOMER_SERVICE_AGENT,
        )
    ),
):
    service = MeterService(db)

    items, total = service.list_meters(
        connection_id=connection_id,
        meter_type=meter_type,
        meter_status=meter_status,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return MeterPaginationResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
    )


# ============================================================
# GET METER
# ============================================================

@router.get(
    "/{meter_id}",
    response_model=MeterResponse,
)
def get_meter(
    meter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.FIELD_TECHNICIAN,
            UserRole.BILLING_OFFICER,
            UserRole.CUSTOMER_SERVICE_AGENT,
            UserRole.CUSTOMER,
        )
    ),
):
    service = MeterService(db)

    return service.get_meter(meter_id)


# ============================================================
# UPDATE METER
# ============================================================

@router.put(
    "/{meter_id}",
    response_model=MeterResponse,
)
def update_meter(
    meter_id: int,
    data: MeterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.FIELD_TECHNICIAN,
        )
    ),
):
    service = MeterService(db)

    meter = service.update_meter(
        meter_id,
        data,
    )

    db.commit()
    db.refresh(meter)

    return meter


# ============================================================
# REPLACE METER
# ============================================================

@router.post(
    "/{meter_id}/replace",
    response_model=MeterResponse,
)
def replace_meter(
    meter_id: int,
    data: MeterReplace,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.FIELD_TECHNICIAN,
        )
    ),
):
    service = MeterService(db)

    new_meter = service.replace_meter(
        meter_id,
        data,
    )

    db.commit()
    db.refresh(new_meter)

    # Meter Replacement Completed Notification
    notification_service = NotificationService(db)

    notification_service.create_event_notification(
        user_id=current_user.id,
        notification_type=NotificationType.METER_REPLACEMENT_COMPLETED,
        title="Meter Replacement Completed",
        message=(
            f"Meter replacement completed successfully. "
            f"Old meter {meter_id} was replaced with "
            f"new meter {new_meter.id} "
            f"(meter number: {new_meter.meter_number})."
        ),
        background_tasks=background_tasks,
    )

    return new_meter