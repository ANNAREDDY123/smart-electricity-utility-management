from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.meter import Meter
from app.models.meter_reading import MeterReading


class MeterReadingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, reading_id: int) -> MeterReading | None:
        """
        Get a meter reading by its primary key.
        """
        return self.db.get(MeterReading, reading_id)

    def get_by_meter_and_period(
        self,
        meter_id: int,
        billing_period: str,
    ) -> MeterReading | None:
        """
        Get a reading for a specific meter and billing period.
        Used to prevent duplicate monthly readings.
        """
        query = select(MeterReading).where(
            MeterReading.meter_id == meter_id,
            MeterReading.billing_period == billing_period,
        )

        return self.db.scalars(query).first()

    def get_latest_by_meter(
        self,
        meter_id: int,
    ) -> MeterReading | None:
        """
        Get the most recent reading for a meter.
        """
        query = (
            select(MeterReading)
            .where(MeterReading.meter_id == meter_id)
            .order_by(
                desc(MeterReading.reading_date),
                desc(MeterReading.id),
            )
        )

        return self.db.scalars(query).first()

    def create(
        self,
        meter_reading: MeterReading,
    ) -> MeterReading:
        """
        Add a new meter reading to the database.
        """
        self.db.add(meter_reading)
        self.db.flush()
        self.db.refresh(meter_reading)

        return meter_reading

    def list_by_meter(
        self,
        meter_id: int,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "reading_date",
        sort_order: str = "desc",
    ) -> tuple[list[MeterReading], int]:
        """
        Get paginated reading history for a specific meter.
        """

        allowed_sort_columns = {
            "reading_date": MeterReading.reading_date,
            "current_reading": MeterReading.current_reading,
            "units_consumed": MeterReading.units_consumed,
            "billing_period": MeterReading.billing_period,
            "id": MeterReading.id,
        }

        sort_column = allowed_sort_columns.get(
            sort_by,
            MeterReading.reading_date,
        )

        order_clause = (
            asc(sort_column)
            if sort_order.lower() == "asc"
            else desc(sort_column)
        )

        count_query = select(func.count()).select_from(MeterReading).where(
            MeterReading.meter_id == meter_id
        )

        total = self.db.scalar(count_query) or 0

        offset = (page - 1) * limit

        query = (
            select(MeterReading)
            .where(MeterReading.meter_id == meter_id)
            .order_by(order_clause)
            .offset(offset)
            .limit(limit)
        )

        items = list(self.db.scalars(query).all())

        return items, total

    def list_by_connection(
        self,
        connection_id: int,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "reading_date",
        sort_order: str = "desc",
    ) -> tuple[list[MeterReading], int]:
        """
        Get paginated reading history for all meters
        belonging to a specific connection.
        """

        allowed_sort_columns = {
            "reading_date": MeterReading.reading_date,
            "current_reading": MeterReading.current_reading,
            "units_consumed": MeterReading.units_consumed,
            "billing_period": MeterReading.billing_period,
            "id": MeterReading.id,
        }

        sort_column = allowed_sort_columns.get(
            sort_by,
            MeterReading.reading_date,
        )

        order_clause = (
            asc(sort_column)
            if sort_order.lower() == "asc"
            else desc(sort_column)
        )

        count_query = (
            select(func.count())
            .select_from(MeterReading)
            .join(
                Meter,
                Meter.id == MeterReading.meter_id,
            )
            .where(
                Meter.connection_id == connection_id
            )
        )

        total = self.db.scalar(count_query) or 0

        offset = (page - 1) * limit

        query = (
            select(MeterReading)
            .join(
                Meter,
                Meter.id == MeterReading.meter_id,
            )
            .where(
                Meter.connection_id == connection_id
            )
            .order_by(order_clause)
            .offset(offset)
            .limit(limit)
        )

        items = list(self.db.scalars(query).all())

        return items, total