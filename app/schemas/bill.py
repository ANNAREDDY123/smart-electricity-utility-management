from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.bill import BillStatus


class BillGenerateRequest(BaseModel):
    connection_id: int = Field(gt=0)

    billing_month: str = Field(
        min_length=7,
        max_length=7,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    )

    units_consumed: Decimal = Field(gt=0)

    tariff_rate: Decimal = Field(gt=0)

    fixed_charge: Decimal = Field(ge=0)

    tax: Decimal = Field(ge=0)

    late_fee: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )

    discount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )

    due_date: date


class BillUpdate(BaseModel):
    late_fee: Decimal | None = Field(
        default=None,
        ge=0,
    )

    discount: Decimal | None = Field(
        default=None,
        ge=0,
    )

    due_date: date | None = None

    bill_status: BillStatus | None = None


class BillResponse(BaseModel):
    id: int
    connection_id: int
    billing_month: str
    units_consumed: Decimal
    energy_charge: Decimal
    fixed_charge: Decimal
    tax: Decimal
    late_fee: Decimal
    discount: Decimal
    total_amount: Decimal
    due_date: date
    bill_status: BillStatus

    model_config = ConfigDict(from_attributes=True)


class BillPaginationResponse(BaseModel):
    items: list[BillResponse]
    total: int
    page: int
    limit: int