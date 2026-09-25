from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tariff import Tariff, TariffStatus


class TariffRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        tariff_id: int,
    ) -> Tariff | None:
        return self.db.get(
            Tariff,
            tariff_id,
        )

    def create(
        self,
        tariff: Tariff,
    ) -> Tariff:
        self.db.add(tariff)
        self.db.flush()
        self.db.refresh(tariff)

        return tariff

    def update(
        self,
        tariff: Tariff,
    ) -> Tariff:
        self.db.flush()
        self.db.refresh(tariff)

        return tariff

    def delete(
        self,
        tariff: Tariff,
    ) -> None:
        # Level 16: soft delete
        tariff.status = TariffStatus.INACTIVE
        self.db.add(tariff)
        self.db.flush()

    def list_tariffs(
        self,
        connection_type: str | None = None,
        tariff_status: TariffStatus | None = None,
    ) -> list[Tariff]:

        query = select(Tariff)

        # Preserve existing API behavior:
        # normal tariff listing shows only active tariffs.
        if tariff_status is None:
            query = query.where(
                Tariff.status == TariffStatus.ACTIVE
            )
        else:
            query = query.where(
                Tariff.status == tariff_status
            )

        if connection_type:
            query = query.where(
                Tariff.connection_type
                == connection_type
            )

        query = query.order_by(
            Tariff.connection_type.asc(),
            Tariff.minimum_units.asc(),
            Tariff.effective_from.desc(),
        )

        return list(
            self.db.scalars(query).all()
        )

    def find_applicable_tariff(
        self,
        connection_type: str,
        units_consumed: Decimal,
        effective_date: date,
    ) -> Tariff | None:

        query = select(Tariff).where(
            Tariff.connection_type
            == connection_type,

            Tariff.status
            == TariffStatus.ACTIVE,

            Tariff.minimum_units
            <= units_consumed,

            Tariff.effective_from
            <= effective_date,

            (
                Tariff.effective_to.is_(None)
                | (
                    Tariff.effective_to
                    >= effective_date
                )
            ),

            (
                Tariff.maximum_units.is_(None)
                | (
                    Tariff.maximum_units
                    >= units_consumed
                )
            ),
        ).order_by(
            Tariff.minimum_units.desc(),
            Tariff.effective_from.desc(),
        )

        return self.db.scalars(
            query
        ).first()

    def has_overlapping_slab(
        self,
        connection_type: str,
        minimum_units: Decimal,
        maximum_units: Decimal | None,
        effective_from: date,
        effective_to: date | None,
        exclude_tariff_id: int | None = None,
    ) -> bool:

        query = select(Tariff).where(
            Tariff.connection_type
            == connection_type,

            Tariff.status
            == TariffStatus.ACTIVE,

            Tariff.effective_from
            <= (
                effective_to
                if effective_to is not None
                else date.max
            ),

            (
                Tariff.effective_to.is_(None)
                | (
                    Tariff.effective_to
                    >= effective_from
                )
            ),
        )

        if exclude_tariff_id is not None:
            query = query.where(
                Tariff.id
                != exclude_tariff_id
            )

        tariffs = list(
            self.db.scalars(query).all()
        )

        for tariff in tariffs:
            existing_min = tariff.minimum_units
            existing_max = tariff.maximum_units
            new_max = maximum_units

            units_overlap = (
                new_max is None
                or existing_min <= new_max
            ) and (
                existing_max is None
                or minimum_units <= existing_max
            )

            if units_overlap:
                return True

        return False