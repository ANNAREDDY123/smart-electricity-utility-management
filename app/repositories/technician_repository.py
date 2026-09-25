from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.technician import Technician


class TechnicianRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, technician_id: int) -> Technician | None:
        return self.db.get(Technician, technician_id)

    def get_by_employee_id(
        self,
        employee_id: str,
    ) -> Technician | None:
        query = select(Technician).where(
            Technician.employee_id == employee_id
        )

        return self.db.scalars(query).first()

    def list_technicians(
        self,
        availability_status=None,
        specialization: str | None = None,
    ) -> list[Technician]:
        query = select(Technician)

        if availability_status is not None:
            query = query.where(
                Technician.availability_status
                == availability_status
            )

        if specialization is not None:
            query = query.where(
                Technician.specialization == specialization
            )

        query = query.order_by(
            Technician.name.asc(),
            Technician.id.asc(),
        )

        return list(self.db.scalars(query).all())

    def create(self, technician: Technician) -> Technician:
        self.db.add(technician)
        self.db.flush()
        self.db.refresh(technician)

        return technician

    def update(self, technician: Technician) -> Technician:
        self.db.flush()
        self.db.refresh(technician)

        return technician