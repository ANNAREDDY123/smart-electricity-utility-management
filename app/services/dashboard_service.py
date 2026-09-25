from datetime import date, datetime

from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository
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


class DashboardService:
    def __init__(self, db: Session):
        self.repository = DashboardRepository(db)

    def get_dashboard(
        self,
        billing_month: str | None = None,
    ) -> DashboardResponse:

        if billing_month is None:
            billing_month = datetime.now().strftime("%Y-%m")

        return DashboardResponse(
            total_customers=self.repository.get_total_customers(),
            active_connections=self.repository.get_active_connections(),
            disconnected_connections=self.repository.get_disconnected_connections(),
            total_meters=self.repository.get_total_meters(),
            faulty_meters=self.repository.get_faulty_meters(),
            monthly_units_consumed=float(
                self.repository.get_monthly_units_consumed(
                    billing_month
                )
                or 0
            ),
            monthly_revenue=float(
                self.repository.get_monthly_revenue(
                    billing_month
                )
                or 0
            ),
            pending_bills=self.repository.get_pending_bills(),
            overdue_bills=self.repository.get_overdue_bills(),
            open_complaints=self.repository.get_open_complaints(),
            resolved_complaints=self.repository.get_resolved_complaints(),
        )

    def get_daily_collection(
        self,
        collection_date: date,
    ) -> DailyCollectionResponse:

        row = self.repository.get_daily_collection(
            collection_date
        )

        return DailyCollectionResponse(
            collection_date=str(collection_date),
            total_collection=float(
                row.total_collection or 0
            ),
            successful_payments=int(
                row.successful_payments or 0
            ),
        )

    def get_monthly_revenue(
        self,
        billing_month: str,
    ) -> MonthlyRevenueResponse:

        row = self.repository.get_monthly_revenue_report(
            billing_month
        )

        return MonthlyRevenueResponse(
            billing_month=billing_month,
            total_revenue=float(
                row.total_revenue or 0
            ),
            total_bills=int(
                row.total_bills or 0
            ),
            total_units_consumed=float(
                row.total_units_consumed or 0
            ),
        )

    def get_customer_billing(
        self,
    ) -> list[CustomerBillingResponse]:

        rows = self.repository.get_customer_billing()

        result = []

        for row in rows:
            billed = float(
                row.total_billed_amount or 0
            )

            paid = float(
                row.total_paid_amount or 0
            )

            result.append(
                CustomerBillingResponse(
                    customer_id=row.customer_id,
                    customer_number=row.customer_number,
                    customer_name=row.customer_name,
                    total_bills=int(
                        row.total_bills or 0
                    ),
                    total_units_consumed=float(
                        row.total_units_consumed or 0
                    ),
                    total_billed_amount=billed,
                    total_paid_amount=paid,
                    outstanding_amount=billed - paid,
                )
            )

        return result

    def get_connection_consumption(
        self,
    ) -> list[ConnectionConsumptionResponse]:

        rows = self.repository.get_connection_consumption()

        return [
            ConnectionConsumptionResponse(
                connection_id=row.connection_id,
                connection_number=row.connection_number,
                customer_id=row.customer_id,
                units_consumed=float(
                    row.units_consumed or 0
                ),
                total_billed_amount=float(
                    row.total_billed_amount or 0
                ),
            )
            for row in rows
        ]

    def get_technician_performance(
        self,
    ) -> list[TechnicianPerformanceResponse]:

        rows = self.repository.get_technician_performance()

        return [
            TechnicianPerformanceResponse(
                technician_id=row.technician_id,
                technician_name=row.technician_name,
                assigned_complaints=int(
                    row.assigned_complaints or 0
                ),
                resolved_complaints=int(
                    row.resolved_complaints or 0
                ),
                open_complaints=int(
                    row.open_complaints or 0
                ),
            )
            for row in rows
        ]

    def get_complaint_resolution(
        self,
    ) -> ComplaintResolutionResponse:

        (
            total,
            resolved,
            closed,
            open_count,
            average_days,
        ) = self.repository.get_complaint_resolution()

        return ComplaintResolutionResponse(
            total_complaints=int(total or 0),
            resolved_complaints=int(resolved or 0),
            closed_complaints=int(closed or 0),
            open_complaints=int(open_count or 0),
            average_resolution_days=float(
                average_days or 0
            ),
        )

    def get_outstanding_payments(
        self,
    ) -> list[OutstandingPaymentResponse]:

        rows = self.repository.get_outstanding_payments()

        result = []

        for row in rows:
            total = float(
                row.total_amount or 0
            )

            paid = float(
                row.paid_amount or 0
            )

            result.append(
                OutstandingPaymentResponse(
                    bill_id=row.bill_id,
                    connection_id=row.connection_id,
                    billing_month=row.billing_month,
                    due_date=str(row.due_date),
                    total_amount=total,
                    paid_amount=paid,
                    outstanding_amount=total - paid,
                )
            )

        return result