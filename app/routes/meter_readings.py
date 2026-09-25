from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.meter_reading import (
    MeterReadingCreate,
    MeterReadingPaginationResponse,
    MeterReadingResponse,
)
from app.services.meter_reading_service import MeterReadingService
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/meter-readings",
    tags=["Meter Readings"],
)


# ============================================================
# CREATE METER READING
# ============================================================

@router.post(
    "",
    response_model=MeterReadingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_meter_reading(
    data: MeterReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.FIELD_TECHNICIAN,
            UserRole.BILLING_OFFICER,
        )
    ),
):
    """
    Create a new meter reading.

    Allowed roles:
    - Super Admin
    - Field Technician
    - Billing Officer
    """

    service = MeterReadingService(db)

    reading = service.create_reading(data)

    db.commit()

    return reading


# ============================================================
# GET SINGLE METER READING
# ============================================================

@router.get(
    "/{reading_id}",
    response_model=MeterReadingResponse,
)
def get_meter_reading(
    reading_id: int,
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
    """
    Get a single meter reading.

    Allowed roles:
    - Super Admin
    - Field Technician
    - Billing Officer
    - Customer Service Agent
    - Customer
    """

    service = MeterReadingService(db)

    return service.get_reading(reading_id)


# ============================================================
# GET READINGS BY METER
# ============================================================

@router.get(
    "/meter/{meter_id}",
    response_model=MeterReadingPaginationResponse,
)
def get_meter_readings(
    meter_id: int,
    page: int = Query(
        default=1,
        ge=1,
        description="Page number",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of records per page",
    ),
    sort_by: str = Query(
        default="reading_date",
        description="Sort field: reading_date, current_reading, units_consumed, billing_period, id",
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order: asc or desc",
    ),
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
    """
    Get paginated meter reading history for a meter.

    Allowed roles:
    - Super Admin
    - Field Technician
    - Billing Officer
    - Customer Service Agent
    - Customer
    """

    service = MeterReadingService(db)

    items, total = service.list_meter_readings(
        meter_id=meter_id,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return MeterReadingPaginationResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
    )


# ============================================================
# GET READINGS BY CONNECTION
# ============================================================

@router.get(
    "/connection/{connection_id}",
    response_model=MeterReadingPaginationResponse,
)
def get_connection_readings(
    connection_id: int,
    page: int = Query(
        default=1,
        ge=1,
        description="Page number",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of records per page",
    ),
    sort_by: str = Query(
        default="reading_date",
        description="Sort field: reading_date, current_reading, units_consumed, billing_period, id",
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order: asc or desc",
    ),
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
    """
    Get paginated meter reading history for a connection.

    Allowed roles:
    - Super Admin
    - Field Technician
    - Billing Officer
    - Customer Service Agent
    - Customer
    """

    service = MeterReadingService(db)

    items, total = service.list_connection_readings(
        connection_id=connection_id,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return MeterReadingPaginationResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
    )