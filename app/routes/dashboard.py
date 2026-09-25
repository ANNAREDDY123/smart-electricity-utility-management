from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.dashboard import (
    ComplaintResolutionResponse,
    ConnectionConsumptionResponse,
    CustomerBillingResponse,
    DailyCollectionResponse,
    DashboardResponse,
    MonthlyRevenueResponse,
    OutstandingPaymentResponse,
    TechnicianPerformanceResponse,
)
from app.services.dashboard_service import DashboardService
from app.utils.dependencies import require_roles


router = APIRouter(
    tags=["Dashboard & Reports"],
)


allowed_roles = (
    "Super Admin",
    "Billing Officer",
    "Customer Service Agent",
)


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
)
def get_dashboard(
    billing_month: str | None = Query(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):
    service = DashboardService(db)

    return service.get_dashboard(
        billing_month=billing_month
    )


@router.get(
    "/reports/daily-collection",
    response_model=DailyCollectionResponse,
)
def get_daily_collection_report(
    report_date: date | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):
    service = DashboardService(db)

    if report_date is None:
        report_date = date.today()

    return service.get_daily_collection(
        collection_date=report_date
    )


@router.get(
    "/reports/monthly-revenue",
    response_model=MonthlyRevenueResponse,
)
def get_monthly_revenue_report(
    billing_month: str | None = Query(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):
    service = DashboardService(db)

    if billing_month is None:
        billing_month = datetime.now().strftime(
            "%Y-%m"
        )

    return service.get_monthly_revenue(
        billing_month=billing_month
    )


@router.get(
    "/reports/customers/billing",
    response_model=list[CustomerBillingResponse],
)
def get_customer_billing_report(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):
    service = DashboardService(db)

    return service.get_customer_billing()


@router.get(
    "/reports/connections/consumption",
    response_model=list[
        ConnectionConsumptionResponse
    ],
)
def get_connection_consumption_report(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):
    service = DashboardService(db)

    return service.get_connection_consumption()


@router.get(
    "/reports/technicians/performance",
    response_model=list[
        TechnicianPerformanceResponse
    ],
)
def get_technician_performance_report(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):
    service = DashboardService(db)

    return service.get_technician_performance()


@router.get(
    "/reports/complaints/resolution",
    response_model=ComplaintResolutionResponse,
)
def get_complaint_resolution_report(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):
    service = DashboardService(db)

    return service.get_complaint_resolution()


@router.get(
    "/reports/outstanding-payments",
    response_model=list[
        OutstandingPaymentResponse
    ],
)
def get_outstanding_payment_report(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*allowed_roles)
    ),
):
    service = DashboardService(db)

    return service.get_outstanding_payments()