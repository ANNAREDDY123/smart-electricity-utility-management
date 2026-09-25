from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.connection import Connection, ConnectionStatus
from app.models.meter import Meter, MeterStatus
from app.repositories.meter_repository import MeterRepository
from app.schemas.meter import MeterCreate, MeterReplace, MeterUpdate


class MeterService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = MeterRepository(db)

    # ========================================================
    # GET METER
    # ========================================================

    def get_meter(self, meter_id: int) -> Meter:
        meter = self.repository.get_by_id(meter_id)

        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found",
            )

        return meter

    # ========================================================
    # CREATE METER
    # ========================================================

    def create_meter(self, data: MeterCreate) -> Meter:
        connection = self.db.get(
            Connection,
            data.connection_id,
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        if connection.status == ConnectionStatus.DISCONNECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot install a meter on a disconnected connection",
            )

        existing_meter = self.repository.get_by_meter_number(
            data.meter_number
        )

        if existing_meter:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Meter number already exists",
            )

        active_meter = self.repository.get_active_by_connection(
            data.connection_id
        )

        if active_meter:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Connection already has an active meter",
            )

        if data.current_reading < data.initial_reading:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current reading cannot be less than initial reading",
            )

        meter = Meter(
            connection_id=data.connection_id,
            meter_number=data.meter_number,
            meter_type=data.meter_type,
            installation_date=data.installation_date,
            initial_reading=data.initial_reading,
            current_reading=data.current_reading,
            meter_status=data.meter_status,
        )

        try:
            return self.repository.create(meter)

        except IntegrityError:
            self.db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Meter number already exists",
            )

    # ========================================================
    # UPDATE METER
    # ========================================================

    def update_meter(
        self,
        meter_id: int,
        data: MeterUpdate,
    ) -> Meter:
        meter = self.get_meter(meter_id)

        if (
            data.current_reading is not None
            and data.current_reading < meter.current_reading
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current reading cannot be less than existing reading",
            )

        if data.meter_status == MeterStatus.ACTIVE:
            active_meter = self.repository.get_active_by_connection(
                meter.connection_id
            )

            if active_meter and active_meter.id != meter.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Connection already has another active meter",
                )

        if data.meter_type is not None:
            meter.meter_type = data.meter_type

        if data.current_reading is not None:
            meter.current_reading = data.current_reading

        if data.meter_status is not None:
            meter.meter_status = data.meter_status

        return meter

    # ========================================================
    # REPLACE METER
    # ========================================================

    def replace_meter(
        self,
        meter_id: int,
        data: MeterReplace,
    ) -> Meter:
        old_meter = self.get_meter(meter_id)

        if old_meter.meter_status == MeterStatus.REMOVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meter has already been removed",
            )

        existing_meter = self.repository.get_by_meter_number(
            data.meter_number
        )

        if existing_meter:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Meter number already exists",
            )

        if data.current_reading < data.initial_reading:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current reading cannot be less than initial reading",
            )

        connection = self.db.get(
            Connection,
            old_meter.connection_id,
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        if connection.status == ConnectionStatus.DISCONNECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot replace meter on a disconnected connection",
            )

        # Mark old meter as removed
        old_meter.meter_status = MeterStatus.REMOVED

        # Create replacement meter
        new_meter = Meter(
            connection_id=old_meter.connection_id,
            meter_number=data.meter_number,
            meter_type=data.meter_type,
            installation_date=data.installation_date,
            initial_reading=data.initial_reading,
            current_reading=data.current_reading,
            meter_status=MeterStatus.ACTIVE,
        )

        try:
            self.db.add(new_meter)
            self.db.flush()
            self.db.refresh(new_meter)

        except IntegrityError:
            self.db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Meter number already exists",
            )

        return new_meter

    # ========================================================
    # LIST METERS
    # ========================================================

    def list_meters(
        self,
        connection_id: int | None = None,
        meter_type: str | None = None,
        meter_status: str | None = None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "id",
        sort_order: str = "desc",
    ) -> tuple[list[Meter], int]:
        return self.repository.list_meters(
            connection_id=connection_id,
            meter_type=meter_type,
            meter_status=meter_status,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )