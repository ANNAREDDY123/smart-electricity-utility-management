from pydantic import BaseModel, ConfigDict, Field

from app.models.technician import TechnicianAvailability


class TechnicianCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    employee_id: str = Field(
        min_length=2,
        max_length=50,
    )

    phone: str = Field(
        min_length=10,
        max_length=20,
    )

    specialization: str = Field(
        min_length=2,
        max_length=100,
    )

    availability_status: TechnicianAvailability = (
        TechnicianAvailability.AVAILABLE
    )


class TechnicianAvailabilityUpdate(BaseModel):
    availability_status: TechnicianAvailability


class TechnicianResponse(BaseModel):
    id: int
    name: str
    employee_id: str
    phone: str
    specialization: str
    availability_status: TechnicianAvailability

    model_config = ConfigDict(from_attributes=True)