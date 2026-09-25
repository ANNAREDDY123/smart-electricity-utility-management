from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.meter import Meter, MeterStatus


class MeterRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, meter_id: int) -> Meter | None:
        return self.db.get(Meter, meter_id)

    def get_by_meter_number(
        self,
        meter_number: str,
    ) -> Meter | None:
        statement = select(Meter).where(
            Meter.meter_number == meter_number
        )
        return self.db.scalar(statement)

    def get_active_by_connection(
        self,
        connection_id: int,
    ) -> Meter | None:
        statement = select(Meter).where(
            Meter.connection_id == connection_id,
            Meter.meter_status == MeterStatus.ACTIVE,
        )
        return self.db.scalar(statement)

    def create(self, meter: Meter) -> Meter:
        self.db.add(meter)
        self.db.flush()
        self.db.refresh(meter)
        return meter

    def update(self, meter: Meter) -> Meter:
        self.db.flush()
        self.db.refresh(meter)
        return meter

    def list_meters(
        self,
        connection_id: int | None = None,
        meter_type: str | None = None,
        meter_status: MeterStatus | None = None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "id",
        sort_order: str = "asc",
    ) -> tuple[list[Meter], int]:

        query = select(Meter)

        if connection_id is not None:
            query = query.where(
                Meter.connection_id == connection_id
            )

        if meter_type is not None:
            query = query.where(
                Meter.meter_type == meter_type
            )

        if meter_status is not None:
            query = query.where(
                Meter.meter_status == meter_status
            )

        allowed_sort_fields = {
            "id": Meter.id,
            "meter_number": Meter.meter_number,
            "meter_type": Meter.meter_type,
            "installation_date": Meter.installation_date,
            "current_reading": Meter.current_reading,
            "meter_status": Meter.meter_status,
        }

        sort_column = allowed_sort_fields.get(
            sort_by,
            Meter.id,
        )

        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        count_query = select(Meter)

        if connection_id is not None:
            count_query = count_query.where(
                Meter.connection_id == connection_id
            )

        if meter_type is not None:
            count_query = count_query.where(
                Meter.meter_type == meter_type
            )

        if meter_status is not None:
            count_query = count_query.where(
                Meter.meter_status == meter_status
            )

        total = len(self.db.scalars(count_query).all())

        offset = (page - 1) * limit

        meters = self.db.scalars(
            query.offset(offset).limit(limit)
        ).all()

        return meters, total