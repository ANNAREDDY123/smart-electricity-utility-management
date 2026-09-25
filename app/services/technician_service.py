from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.technician import Technician
from app.repositories.technician_repository import (
    TechnicianRepository,
)
from app.schemas.technician import (
    TechnicianAvailabilityUpdate,
    TechnicianCreate,
)


class TechnicianService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TechnicianRepository(db)

    def get_technician(
        self,
        technician_id: int,
    ) -> Technician:
        technician = self.repository.get_by_id(technician_id)

        if not technician:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Technician not found",
            )

        return technician

    def create_technician(
        self,
        data: TechnicianCreate,
    ) -> Technician:
        existing = self.repository.get_by_employee_id(
            data.employee_id
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee ID already exists",
            )

        technician = Technician(
            name=data.name,
            employee_id=data.employee_id,
            phone=data.phone,
            specialization=data.specialization,
            availability_status=data.availability_status,
        )

        technician = self.repository.create(technician)

        self.db.flush()

        return technician

    def list_technicians(
        self,
        availability_status=None,
        specialization: str | None = None,
    ) -> list[Technician]:
        return self.repository.list_technicians(
            availability_status=availability_status,
            specialization=specialization,
        )

    def update_availability(
        self,
        technician_id: int,
        data: TechnicianAvailabilityUpdate,
    ) -> Technician:
        technician = self.get_technician(technician_id)

        technician.availability_status = (
            data.availability_status
        )

        technician = self.repository.update(technician)

        self.db.flush()

        return technician