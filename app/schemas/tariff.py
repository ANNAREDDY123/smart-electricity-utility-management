from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.tariff import TariffStatus


class TariffCreate(BaseModel):
    tariff_name: str = Field(
        min_length=2,
        max_length=100,
    )

    connection_type: str = Field(
        min_length=1,
        max_length=30,
    )

    minimum_units: Decimal = Field(
        ge=0,
    )

    maximum_units: Decimal | None = Field(
        default=None,
        ge=0,
    )

    rate_per_unit: Decimal = Field(
        gt=0,
    )

    fixed_charge: Decimal = Field(
        ge=0,
    )

    effective_from: date

    effective_to: date | None = None

    status: TariffStatus = TariffStatus.ACTIVE

    @model_validator(mode="after")
    def validate_tariff(self):
        if (
            self.maximum_units is not None
            and self.maximum_units < self.minimum_units
        ):
            raise ValueError(
                "maximum_units cannot be less than minimum_units"
            )

        if (
            self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError(
                "effective_to cannot be earlier than effective_from"
            )

        return self


class TariffUpdate(BaseModel):
    tariff_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    connection_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    minimum_units: Decimal | None = Field(
        default=None,
        ge=0,
    )

    maximum_units: Decimal | None = Field(
        default=None,
        ge=0,
    )

    rate_per_unit: Decimal | None = Field(
        default=None,
        gt=0,
    )

    fixed_charge: Decimal | None = Field(
        default=None,
        ge=0,
    )

    effective_from: date | None = None

    effective_to: date | None = None

    status: TariffStatus | None = None


class TariffResponse(BaseModel):
    id: int
    tariff_name: str
    connection_type: str
    minimum_units: Decimal
    maximum_units: Decimal | None
    rate_per_unit: Decimal
    fixed_charge: Decimal
    effective_from: date
    effective_to: date | None
    status: TariffStatus

    model_config = ConfigDict(
        from_attributes=True
    )


class TariffApplyResponse(BaseModel):
    tariff_id: int
    tariff_name: str
    connection_type: str
    units_consumed: Decimal
    rate_per_unit: Decimal
    fixed_charge: Decimal
    effective_from: date
    effective_to: date | None