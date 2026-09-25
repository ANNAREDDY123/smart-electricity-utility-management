from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.connection import Connection
from app.repositories.analytics_repository import (
    AnalyticsRepository,
)
from app.schemas.analytics import (
    AverageMonthlyConsumptionResponse,
    ConnectionUsageResponse,
    CustomerUsageResponse,
    HighestConsumptionResponse,
    MonthlyConsumptionResponse,
    YearlyConsumptionResponse,
)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AnalyticsRepository(db)

    def _validate_connection(
        self,
        connection_id: int,
    ) -> None:
        connection = self.db.get(
            Connection,
            connection_id,
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

    def get_connection_monthly(
        self,
        connection_id: int,
    ) -> list[MonthlyConsumptionResponse]:
        self._validate_connection(connection_id)

        rows = self.repository.get_connection_monthly(
            connection_id
        )

        return [
            MonthlyConsumptionResponse(
                month=row.month,
                units_consumed=Decimal(
                    str(row.units_consumed or 0)
                ),
                bill_amount=Decimal(
                    str(row.bill_amount or 0)
                ),
            )
            for row in rows
        ]

    def get_connection_yearly(
        self,
        connection_id: int,
    ) -> list[YearlyConsumptionResponse]:
        self._validate_connection(connection_id)

        rows = self.repository.get_connection_yearly(
            connection_id
        )

        return [
            YearlyConsumptionResponse(
                year=int(row.year),
                units_consumed=Decimal(
                    str(row.units_consumed or 0)
                ),
                bill_amount=Decimal(
                    str(row.bill_amount or 0)
                ),
            )
            for row in rows
        ]

    def get_connection_usage(
        self,
    ) -> list[ConnectionUsageResponse]:
        rows = self.repository.get_connection_usage()

        return [
            ConnectionUsageResponse(
                connection_id=row.connection_id,
                connection_number=row.connection_number,
                units_consumed=Decimal(
                    str(row.units_consumed or 0)
                ),
                bill_amount=Decimal(
                    str(row.bill_amount or 0)
                ),
            )
            for row in rows
        ]

    def get_customer_usage(
        self,
    ) -> list[CustomerUsageResponse]:
        rows = self.repository.get_customer_usage()

        return [
            CustomerUsageResponse(
                customer_id=row.customer_id,
                customer_number=row.customer_number,
                customer_name=row.customer_name,
                units_consumed=Decimal(
                    str(row.units_consumed or 0)
                ),
                bill_amount=Decimal(
                    str(row.bill_amount or 0)
                ),
            )
            for row in rows
        ]

    def get_highest_consuming_connections(
        self,
        limit: int = 10,
    ) -> list[HighestConsumptionResponse]:
        rows = (
            self.repository
            .get_highest_consuming_connections(limit)
        )

        return [
            HighestConsumptionResponse(
                connection_id=row.connection_id,
                connection_number=row.connection_number,
                units_consumed=Decimal(
                    str(row.units_consumed or 0)
                ),
                bill_amount=Decimal(
                    str(row.bill_amount or 0)
                ),
            )
            for row in rows
        ]

    def get_average_monthly_consumption(
        self,
    ) -> AverageMonthlyConsumptionResponse:
        average = (
            self.repository
            .get_average_monthly_consumption()
        )

        return AverageMonthlyConsumptionResponse(
            average_monthly_consumption=Decimal(
                str(average or 0)
            )
        )