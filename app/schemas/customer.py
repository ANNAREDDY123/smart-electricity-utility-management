from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.customer import CustomerStatus


class CustomerCreate(BaseModel):
    customer_number: str = Field(
        min_length=2,
        max_length=50,
    )
    full_name: str = Field(
        min_length=2,
        max_length=150,
    )
    email: EmailStr
    phone: str = Field(
        min_length=7,
        max_length=20,
    )
    address: str = Field(
        min_length=3,
        max_length=255,
    )
    city: str = Field(
        min_length=2,
        max_length=100,
    )


class CustomerUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    email: EmailStr | None = None
    phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=20,
    )
    address: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
    )
    city: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    status: CustomerStatus | None = None


class CustomerResponse(BaseModel):
    id: int
    customer_number: str
    full_name: str
    email: EmailStr
    phone: str
    address: str
    city: str
    status: CustomerStatus

    model_config = ConfigDict(from_attributes=True)