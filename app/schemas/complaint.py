from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.complaint import (
    ComplaintPriority,
    ComplaintStatus,
    ComplaintType,
)


class ComplaintCreate(BaseModel):
    customer_id: int = Field(gt=0)
    connection_id: int = Field(gt=0)

    complaint_type: ComplaintType

    description: str = Field(
        min_length=5,
        max_length=2000,
    )

    priority: ComplaintPriority = ComplaintPriority.MEDIUM


class ComplaintAssign(BaseModel):
    assigned_to: int = Field(gt=0)


class ComplaintStatusUpdate(BaseModel):
    status: ComplaintStatus

    remarks: str | None = Field(
        default=None,
        max_length=500,
    )


class ComplaintResponse(BaseModel):
    id: int
    customer_id: int
    connection_id: int
    complaint_type: ComplaintType
    description: str
    priority: ComplaintPriority
    assigned_to: int | None
    status: ComplaintStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ComplaintHistoryResponse(BaseModel):
    id: int
    complaint_id: int
    old_status: ComplaintStatus | None
    new_status: ComplaintStatus
    changed_by: int
    remarks: str | None
    changed_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ComplaintDetailResponse(ComplaintResponse):
    history: list[ComplaintHistoryResponse] = []

from typing import Generic, TypeVar

T = TypeVar("T")


class ComplaintPaginationResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int
    pages: int