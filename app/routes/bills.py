from decimal import Decimal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.bill import BillStatus
from app.models.notification import NotificationType
from app.schemas.bill import (
    BillGenerateRequest,
    BillPaginationResponse,
    BillResponse,
    BillUpdate,
)
from app.services.bill_service import BillService
from app.services.notification_service import NotificationService
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/bills",
    tags=["Bills"],
)


# ============================================================
# GENERATE BILL
# ============================================================

@router.post(
    "/generate",
    response_model=BillResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_bill(
    data: BillGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Billing Officer",
        )
    ),
):
    service = BillService(db)

    bill = service.generate_bill(data)

    db.commit()
    db.refresh(bill)

    notification_service = NotificationService(db)

    notification_service.create_event_notification(
        user_id=current_user.id,
        notification_type=NotificationType.BILL_GENERATED,
        title="Bill Generated",
        message=(
            f"Electricity bill {bill.id} for "
            f"billing month {bill.billing_month} "
            "has been generated successfully."
        ),
        background_tasks=background_tasks,
    )

    return bill


# ============================================================
# BILL DUE REMINDER
# ============================================================

@router.post(
    "/{bill_id}/due-reminder",
    status_code=status.HTTP_202_ACCEPTED,
)
def send_bill_due_reminder(
    bill_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Billing Officer",
        )
    ),
):
    service = BillService(db)

    bill = service.get_bill(bill_id)

    notification_service = NotificationService(db)

    notification_service.create_event_notification(
        user_id=current_user.id,
        notification_type=NotificationType.BILL_DUE_REMINDER,
        title="Bill Due Reminder",
        message=(
            f"Electricity bill {bill.id} "
            f"for billing month {bill.billing_month} "
            f"is due on {bill.due_date}."
        ),
        background_tasks=background_tasks,
    )

    return {
        "message": "Bill due reminder notification scheduled",
        "bill_id": bill.id,
    }


# ============================================================
# BILL OVERDUE NOTIFICATION
# ============================================================

@router.post(
    "/{bill_id}/overdue-notification",
    status_code=status.HTTP_202_ACCEPTED,
)
def send_bill_overdue_notification(
    bill_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Billing Officer",
        )
    ),
):
    service = BillService(db)

    bill = service.get_bill(bill_id)

    notification_service = NotificationService(db)

    notification_service.create_event_notification(
        user_id=current_user.id,
        notification_type=NotificationType.BILL_OVERDUE,
        title="Bill Overdue",
        message=(
            f"Electricity bill {bill.id} "
            f"for billing month {bill.billing_month} "
            f"was due on {bill.due_date} and is overdue."
        ),
        background_tasks=background_tasks,
    )

    return {
        "message": "Bill overdue notification scheduled",
        "bill_id": bill.id,
    }


# ============================================================
# LIST BILLS
# ============================================================

@router.get(
    "",
    response_model=BillPaginationResponse,
)
def list_bills(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    billing_month: str | None = Query(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    ),
    bill_status: BillStatus | None = None,
    min_amount: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    max_amount: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    sort_by: str = Query(default="id"),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Billing Officer",
            "Customer Service Agent",
        )
    ),
):
    service = BillService(db)

    bills, total = service.list_bills(
        page=page,
        limit=limit,
        billing_month=billing_month,
        bill_status=bill_status,
        min_amount=min_amount,
        max_amount=max_amount,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return {
        "items": bills,
        "total": total,
        "page": page,
        "limit": limit,
    }


# ============================================================
# CUSTOMER BILLS
# Assignment-required path:
# GET /customers/{customer_id}/bills
# ============================================================

customer_bills_router = APIRouter(
    tags=["Bills"],
)


@customer_bills_router.get(
    "/customers/{customer_id}/bills",
    response_model=BillPaginationResponse,
)
def get_customer_bills(
    customer_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    billing_month: str | None = Query(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    ),
    bill_status: BillStatus | None = None,
    sort_by: str = Query(default="billing_month"),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Billing Officer",
            "Customer Service Agent",
            "Customer",
        )
    ),
):
    service = BillService(db)

    bills, total = service.list_customer_bills(
        customer_id=customer_id,
        page=page,
        limit=limit,
        billing_month=billing_month,
        bill_status=bill_status,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return {
        "items": bills,
        "total": total,
        "page": page,
        "limit": limit,
    }


# ============================================================
# CONNECTION BILLS
# Assignment-required path:
# GET /connections/{connection_id}/bills
# ============================================================

connection_bills_router = APIRouter(
    tags=["Bills"],
)


@connection_bills_router.get(
    "/connections/{connection_id}/bills",
    response_model=BillPaginationResponse,
)
def get_connection_bills(
    connection_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query(default="billing_month"),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Billing Officer",
            "Customer Service Agent",
            "Customer",
        )
    ),
):
    service = BillService(db)

    bills, total = service.list_connection_bills(
        connection_id=connection_id,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return {
        "items": bills,
        "total": total,
        "page": page,
        "limit": limit,
    }


# ============================================================
# GET SINGLE BILL
# ============================================================

@router.get(
    "/{bill_id}",
    response_model=BillResponse,
)
def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Billing Officer",
            "Customer Service Agent",
            "Customer",
        )
    ),
):
    service = BillService(db)

    return service.get_bill(bill_id)


# ============================================================
# UPDATE BILL
# ============================================================

@router.put(
    "/{bill_id}",
    response_model=BillResponse,
)
def update_bill(
    bill_id: int,
    data: BillUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Billing Officer",
        )
    ),
):
    service = BillService(db)

    bill = service.update_bill(
        bill_id,
        data,
    )

    db.commit()
    db.refresh(bill)

    return bill