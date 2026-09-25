from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.meter import MeterStatus


class MeterCreate(BaseModel):
    connection_id: int = Field(gt=0)
    meter_number: str = Field(min_length=1, max_length=50)
    meter_type: str = Field(min_length=1, max_length=100)
    installation_date: date
    initial_reading: Decimal = Field(ge=0)
    current_reading: Decimal = Field(ge=0)
    meter_status: MeterStatus = MeterStatus.ACTIVE


class MeterUpdate(BaseModel):
    meter_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    current_reading: Decimal | None = Field(
        default=None,
        ge=0,
    )
    meter_status: MeterStatus | None = None


class MeterReplace(BaseModel):
    # Supports both:
    # "meter_number" - current Level 5 workflow
    # "new_meter_number" - existing Level 4 workflow
    meter_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    new_meter_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    meter_type: str = Field(
        min_length=1,
        max_length=100,
    )
    installation_date: date
    initial_reading: Decimal = Field(ge=0)
    current_reading: Decimal = Field(ge=0)

    @model_validator(mode="after")
    def validate_meter_number(self):
        if not self.meter_number and not self.new_meter_number:
            raise ValueError(
                "Either meter_number or new_meter_number is required"
            )

        if self.meter_number and self.new_meter_number:
            if self.meter_number != self.new_meter_number:
                raise ValueError(
                    "meter_number and new_meter_number must match"
                )

        if not self.meter_number:
            self.meter_number = self.new_meter_number

        return self


class MeterResponse(BaseModel):
    id: int
    connection_id: int
    meter_number: str
    meter_type: str
    installation_date: date
    initial_reading: Decimal
    current_reading: Decimal
    meter_status: MeterStatus

    model_config = ConfigDict(from_attributes=True)


class MeterPaginationResponse(BaseModel):
    items: list[MeterResponse]
    total: int
    page: int
    limit: int