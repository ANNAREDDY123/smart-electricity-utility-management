from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.meter import Meter, MeterStatus
from app.models.meter_reading import MeterReading
from app.repositories.meter_reading_repository import MeterReadingRepository
from app.schemas.meter_reading import MeterReadingCreate


class MeterReadingService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = MeterReadingRepository(db)

    def _get_meter(self, meter_id: int) -> Meter:
        """
        Get the meter or raise 404 if it does not exist.
        """
        meter = self.db.get(Meter, meter_id)

        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found",
            )

        return meter

    def _get_billing_period(self, reading_date: date) -> str:
        """
        Convert reading date to YYYY-MM billing period.
        Example:
            2026-09-23 -> 2026-09
        """
        return reading_date.strftime("%Y-%m")

    def create_reading(
        self,
        data: MeterReadingCreate,
    ) -> MeterReading:
        """
        Create a meter reading and update the meter's current reading.

        Business rules:
        1. Meter must exist.
        2. Meter must be Active.
        3. Current reading cannot be less than previous reading.
        4. Duplicate meter + billing period is not allowed.
        5. A new reading cannot be lower than the latest meter reading.
        6. Units consumed = current reading - previous reading.
        7. Meter current_reading is updated after successful reading creation.
        """

        meter = self._get_meter(data.meter_id)

        # ---------------------------------------------------------
        # 1. Only active meters can receive readings
        # ---------------------------------------------------------
        if meter.meter_status != MeterStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active meters can receive readings",
            )

        # ---------------------------------------------------------
        # 2. Validate current reading against previous reading
        # ---------------------------------------------------------
        if data.current_reading < data.previous_reading:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Current reading cannot be less than previous reading",
            )

        # ---------------------------------------------------------
        # 3. Determine billing period
        # ---------------------------------------------------------
        billing_period = self._get_billing_period(data.reading_date)

        # ---------------------------------------------------------
        # 4. Prevent duplicate billing-period reading
        # ---------------------------------------------------------
        existing_reading = self.repository.get_by_meter_and_period(
            meter_id=data.meter_id,
            billing_period=billing_period,
        )

        if existing_reading:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A reading already exists for this meter "
                    f"for billing period {billing_period}"
                ),
            )

        # ---------------------------------------------------------
        # 5. Validate against the latest reading
        # ---------------------------------------------------------
        latest_reading = self.repository.get_latest_by_meter(
            meter_id=data.meter_id
        )

        if latest_reading:
            if data.current_reading < latest_reading.current_reading:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Current reading cannot be less than "
                        "the meter's latest reading"
                    ),
                )

        # ---------------------------------------------------------
        # 6. Calculate units consumed
        # ---------------------------------------------------------
        units_consumed = (
            data.current_reading - data.previous_reading
        )

        if units_consumed < Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Units consumed cannot be negative",
            )

        # ---------------------------------------------------------
        # 7. Create MeterReading object
        # ---------------------------------------------------------
        meter_reading = MeterReading(
            meter_id=data.meter_id,
            reading_date=data.reading_date,
            previous_reading=data.previous_reading,
            current_reading=data.current_reading,
            units_consumed=units_consumed,
            reading_source=data.reading_source,
            remarks=data.remarks,
            billing_period=billing_period,
        )

        # ---------------------------------------------------------
        # 8. Update meter's current reading
        # ---------------------------------------------------------
        meter.current_reading = data.current_reading

        try:
            # Add both changes to the current transaction.
            self.db.add(meter_reading)

            # Flush sends the changes to the database without
            # committing the transaction.
            self.db.flush()

            # Refresh the reading so generated fields are available.
            self.db.refresh(meter_reading)

        except IntegrityError:
            # Roll back the transaction if the database rejects
            # the operation, for example because of the unique
            # meter + billing_period constraint.
            self.db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate meter reading for this billing period",
            )

        return meter_reading

    def get_reading(
        self,
        reading_id: int,
    ) -> MeterReading:
        """
        Get a single meter reading.
        """
        reading = self.repository.get_by_id(reading_id)

        if not reading:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter reading not found",
            )

        return reading

    def list_meter_readings(
        self,
        meter_id: int,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "reading_date",
        sort_order: str = "desc",
    ) -> tuple[list[MeterReading], int]:
        """
        Get paginated readings for a meter.
        """

        # Make sure the meter exists.
        self._get_meter(meter_id)

        return self.repository.list_by_meter(
            meter_id=meter_id,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def list_connection_readings(
        self,
        connection_id: int,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "reading_date",
        sort_order: str = "desc",
    ) -> tuple[list[MeterReading], int]:
        """
        Get paginated readings for all meters belonging
        to a connection.
        """

        # Verify that at least one meter exists for this connection.
        meter_exists = (
            self.db.query(Meter.id)
            .filter(Meter.connection_id == connection_id)
            .first()
        )

        if not meter_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No meter found for this connection",
            )

        return self.repository.list_by_connection(
            connection_id=connection_id,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )