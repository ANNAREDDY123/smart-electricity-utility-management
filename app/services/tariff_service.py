from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.tariff import Tariff, TariffStatus
from app.repositories.tariff_repository import (
    TariffRepository,
)
from app.schemas.tariff import (
    TariffCreate,
    TariffUpdate,
)


class TariffService:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.repository = TariffRepository(db)

    def get_tariff(
        self,
        tariff_id: int,
    ) -> Tariff:

        tariff = self.repository.get_by_id(
            tariff_id
        )

        if not tariff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tariff not found",
            )

        return tariff

    def create_tariff(
        self,
        data: TariffCreate,
    ) -> Tariff:

        if data.status == TariffStatus.ACTIVE:
            if self.repository.has_overlapping_slab(
                connection_type=data.connection_type,
                minimum_units=data.minimum_units,
                maximum_units=data.maximum_units,
                effective_from=data.effective_from,
                effective_to=data.effective_to,
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Tariff slab overlaps with "
                        "an existing active tariff"
                    ),
                )

        tariff = Tariff(
            tariff_name=data.tariff_name,
            connection_type=data.connection_type,
            minimum_units=data.minimum_units,
            maximum_units=data.maximum_units,
            rate_per_unit=data.rate_per_unit,
            fixed_charge=data.fixed_charge,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            status=data.status,
        )

        return self.repository.create(tariff)

    def update_tariff(
        self,
        tariff_id: int,
        data: TariffUpdate,
    ) -> Tariff:

        tariff = self.get_tariff(
            tariff_id
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        connection_type = update_data.get(
            "connection_type",
            tariff.connection_type,
        )

        minimum_units = update_data.get(
            "minimum_units",
            tariff.minimum_units,
        )

        maximum_units = update_data.get(
            "maximum_units",
            tariff.maximum_units,
        )

        effective_from = update_data.get(
            "effective_from",
            tariff.effective_from,
        )

        effective_to = update_data.get(
            "effective_to",
            tariff.effective_to,
        )

        new_status = update_data.get(
            "status",
            tariff.status,
        )

        if new_status == TariffStatus.ACTIVE:
            if self.repository.has_overlapping_slab(
                connection_type=connection_type,
                minimum_units=minimum_units,
                maximum_units=maximum_units,
                effective_from=effective_from,
                effective_to=effective_to,
                exclude_tariff_id=tariff.id,
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Tariff slab overlaps with "
                        "an existing active tariff"
                    ),
                )

        if (
            maximum_units is not None
            and maximum_units < minimum_units
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "maximum_units cannot be "
                    "less than minimum_units"
                ),
            )

        if (
            effective_to is not None
            and effective_to < effective_from
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "effective_to cannot be "
                    "earlier than effective_from"
                ),
            )

        for field, value in update_data.items():
            setattr(
                tariff,
                field,
                value,
            )

        return self.repository.update(
            tariff
        )

    def delete_tariff(
        self,
        tariff_id: int,
    ) -> None:

        tariff = self.get_tariff(
            tariff_id
        )

        # Level 16: soft delete
        tariff.status = TariffStatus.INACTIVE

        self.repository.update(
            tariff
        )

    def list_tariffs(
        self,
        connection_type: str | None = None,
        tariff_status: TariffStatus | None = None,
    ) -> list[Tariff]:

        return self.repository.list_tariffs(
            connection_type=connection_type,
            tariff_status=tariff_status,
        )

    def apply_tariff(
        self,
        connection_type: str,
        units_consumed: Decimal,
        effective_date: date,
    ) -> Tariff:

        if units_consumed < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Units consumed cannot be negative",
            )

        tariff = (
            self.repository.find_applicable_tariff(
                connection_type=connection_type,
                units_consumed=units_consumed,
                effective_date=effective_date,
            )
        )

        if not tariff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No applicable active tariff "
                    "found for the supplied "
                    "connection type, units, "
                    "and effective date"
                ),
            )

        return tariff