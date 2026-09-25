from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)

    payment_method: PaymentMethod

    transaction_id: str = Field(
        min_length=3,
        max_length=100,
    )

    payment_date: datetime | None = None

    payment_status: PaymentStatus = PaymentStatus.SUCCESS


class PaymentResponse(BaseModel):
    id: int
    bill_id: int
    amount: Decimal
    payment_method: PaymentMethod
    transaction_id: str
    payment_date: datetime
    payment_status: PaymentStatus

    model_config = ConfigDict(
        from_attributes=True
    )


class PaymentPaginationResponse(BaseModel):
    items: list[PaymentResponse]
    total: int
    page: int
    limit: int