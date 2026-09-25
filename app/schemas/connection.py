from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.connection import ConnectionStatus, ConnectionType


class ConnectionCreate(BaseModel):
    customer_id: int = Field(gt=0)
    connection_number: str = Field(
        min_length=2,
        max_length=50,
    )
    connection_type: ConnectionType
    sanctioned_load: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    tariff_type: str = Field(
        min_length=2,
        max_length=100,
    )
    connection_date: date
    status: ConnectionStatus = ConnectionStatus.ACTIVE


class ConnectionUpdate(BaseModel):
    connection_type: ConnectionType | None = None
    sanctioned_load: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    tariff_type: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    connection_date: date | None = None
    status: ConnectionStatus | None = None


class ConnectionResponse(BaseModel):
    id: int
    customer_id: int
    connection_number: str
    connection_type: ConnectionType
    sanctioned_load: Decimal
    tariff_type: str
    connection_date: date
    status: ConnectionStatus

    model_config = ConfigDict(from_attributes=True)