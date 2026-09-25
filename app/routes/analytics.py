from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analytics import (
    AverageMonthlyConsumptionResponse,
    ConnectionUsageResponse,
    CustomerUsageResponse,
    HighestConsumptionResponse,
    MonthlyConsumptionResponse,
    YearlyConsumptionResponse,
)
from app.services.analytics_service import AnalyticsService
from app.utils.dependencies import get_current_active_user


router = APIRouter(
    prefix="/analytics",
    tags=["Consumption Analytics"],
)


# ------------------------------------------------------------
# Static routes MUST come before /connections/{connection_id}/...
# ------------------------------------------------------------

@router.get(
    "/connections/usage",
    response_model=list[ConnectionUsageResponse],
)
def get_connection_usage(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AnalyticsService(db)

    return service.get_connection_usage()


@router.get(
    "/customers/usage",
    response_model=list[CustomerUsageResponse],
)
def get_customer_usage(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AnalyticsService(db)

    return service.get_customer_usage()


@router.get(
    "/connections/highest-consumption",
    response_model=list[HighestConsumptionResponse],
)
def get_highest_consuming_connections(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AnalyticsService(db)

    return service.get_highest_consuming_connections(
        limit
    )


@router.get(
    "/consumption/average-monthly",
    response_model=AverageMonthlyConsumptionResponse,
)
def get_average_monthly_consumption(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AnalyticsService(db)

    return service.get_average_monthly_consumption()


# ------------------------------------------------------------
# Dynamic routes come AFTER static routes
# ------------------------------------------------------------

@router.get(
    "/connections/{connection_id}/monthly",
    response_model=list[MonthlyConsumptionResponse],
)
def get_connection_monthly(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AnalyticsService(db)

    return service.get_connection_monthly(
        connection_id
    )


@router.get(
    "/connections/{connection_id}/yearly",
    response_model=list[YearlyConsumptionResponse],
)
def get_connection_yearly(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AnalyticsService(db)

    return service.get_connection_yearly(
        connection_id
    )