from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.meter_reading import ReadingSource


class MeterReadingCreate(BaseModel):
    meter_id: int = Field(gt=0)
    reading_date: date
    previous_reading: Decimal = Field(ge=0)
    current_reading: Decimal = Field(ge=0)
    reading_source: ReadingSource
    remarks: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_reading_values(self):
        if self.current_reading < self.previous_reading:
            raise ValueError(
                "Current reading cannot be less than previous reading"
            )

        return self


class MeterReadingResponse(BaseModel):
    id: int
    meter_id: int
    reading_date: date
    previous_reading: Decimal
    current_reading: Decimal
    units_consumed: Decimal
    reading_source: ReadingSource
    remarks: str | None
    billing_period: str

    model_config = ConfigDict(from_attributes=True)


class MeterReadingPaginationResponse(BaseModel):
    items: list[MeterReadingResponse]
    total: int
    page: int
    limit: int