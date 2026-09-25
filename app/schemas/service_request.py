from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.service_request import (
    ServiceRequestStatus,
    ServiceRequestType,
)


class ServiceRequestCreate(BaseModel):
    customer_id: int = Field(gt=0)

    connection_id: int | None = Field(
        default=None,
        gt=0,
    )

    request_type: ServiceRequestType

    description: str = Field(
        min_length=5,
        max_length=2000,
    )

    requested_date: date


class ServiceRequestResponse(BaseModel):
    id: int
    customer_id: int
    connection_id: int | None
    request_type: ServiceRequestType
    description: str
    requested_date: date
    status: ServiceRequestStatus

    model_config = ConfigDict(from_attributes=True)


class ServiceRequestPaginationResponse(BaseModel):
    items: list[ServiceRequestResponse]
    total: int
    page: int
    limit: int