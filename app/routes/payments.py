from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notification import NotificationType
from app.models.payment import PaymentMethod, PaymentStatus
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.notification_service import NotificationService
from app.services.payment_service import PaymentService
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)

bill_payments_router = APIRouter(
    prefix="/bills",
    tags=["Payments"],
)


@router.post(
    "/{bill_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    bill_id: int,
    data: PaymentCreate,
    background_tasks: BackgroundTasks,
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
    service = PaymentService(db)

    payment = service.create_payment(
        bill_id=bill_id,
        data=data,
    )

    db.commit()
    db.refresh(payment)

    # Payment Success Notification
    if payment.payment_status == PaymentStatus.SUCCESS:
        notification_service = NotificationService(db)

        notification_service.create_event_notification(
            user_id=current_user.id,
            notification_type=NotificationType.PAYMENT_SUCCESS,
            title="Payment Success",
            message=(
                f"Payment {payment.id} for bill "
                f"{payment.bill_id} was successful. "
                f"Amount paid: {payment.amount}."
            ),
            background_tasks=background_tasks,
        )

    # Payment Failure Notification
    elif payment.payment_status == PaymentStatus.FAILED:
        notification_service = NotificationService(db)

        notification_service.create_event_notification(
            user_id=current_user.id,
            notification_type=NotificationType.PAYMENT_FAILURE,
            title="Payment Failure",
            message=(
                f"Payment {payment.id} for bill "
                f"{payment.bill_id} failed. "
                f"Amount attempted: {payment.amount}."
            ),
            background_tasks=background_tasks,
        )

    return payment


@router.get(
    "",
    response_model=list[PaymentResponse],
)
def get_payments(
    bill_id: int | None = Query(
        default=None,
        gt=0,
    ),
    payment_status: PaymentStatus | None = None,
    payment_method: PaymentMethod | None = None,
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
    service = PaymentService(db)

    return service.list_payments(
        bill_id=bill_id,
        payment_status=payment_status,
        payment_method=payment_method,
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
)
def get_payment(
    payment_id: int,
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
    service = PaymentService(db)

    return service.get_payment(
        payment_id
    )


@bill_payments_router.get(
    "/{bill_id}/payments",
    response_model=list[PaymentResponse],
)
def get_bill_payments(
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
    service = PaymentService(db)

    return service.list_bill_payments(
        bill_id
    )