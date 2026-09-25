from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.complaint import (
    Complaint,
    ComplaintHistory,
    ComplaintPriority,
    ComplaintStatus,
)
from app.models.connection import Connection
from app.models.customer import Customer
from app.models.user import User, UserRole
from app.repositories.complaint_repository import (
    ComplaintRepository,
)
from app.schemas.complaint import (
    ComplaintAssign,
    ComplaintCreate,
    ComplaintStatusUpdate,
)


class ComplaintService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ComplaintRepository(db)

    def get_customer(
        self,
        customer_id: int,
    ) -> Customer:

        customer = self.db.get(
            Customer,
            customer_id,
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        return customer

    def get_connection(
        self,
        connection_id: int,
    ) -> Connection:

        connection = self.db.get(
            Connection,
            connection_id,
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        return connection

    def get_complaint(
        self,
        complaint_id: int,
    ) -> Complaint:

        complaint = self.repository.get_by_id(
            complaint_id
        )

        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint not found",
            )

        return complaint

    def create_complaint(
        self,
        data: ComplaintCreate,
        current_user: User,
    ) -> Complaint:

        customer = self.get_customer(
            data.customer_id
        )

        connection = self.get_connection(
            data.connection_id
        )

        if connection.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Connection does not belong to customer",
            )

        if current_user.role == UserRole.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customer users cannot create complaints for other customers",
            )

        complaint = Complaint(
            customer_id=data.customer_id,
            connection_id=data.connection_id,
            complaint_type=data.complaint_type,
            description=data.description,
            priority=data.priority,
            status=ComplaintStatus.OPEN,
        )

        complaint = self.repository.create(
            complaint
        )

        history = ComplaintHistory(
            complaint_id=complaint.id,
            old_status=None,
            new_status=ComplaintStatus.OPEN,
            changed_by=current_user.id,
            remarks="Complaint created",
        )

        self.repository.create_history(history)

        self.db.flush()

        return complaint

    def assign_complaint(
        self,
        complaint_id: int,
        data: ComplaintAssign,
        current_user: User,
    ) -> Complaint:

        complaint = self.get_complaint(
            complaint_id
        )

        technician = self.db.get(
            User,
            data.assigned_to,
        )

        if not technician:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Technician not found",
            )

        if technician.role != UserRole.FIELD_TECHNICIAN:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="User is not a Field Technician",
            )

        if not technician.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Technician is not available",
            )

        old_status = complaint.status

        complaint.assigned_to = technician.id

        if complaint.status == ComplaintStatus.OPEN:
            complaint.status = ComplaintStatus.ASSIGNED

        self.repository.update(complaint)

        history = ComplaintHistory(
            complaint_id=complaint.id,
            old_status=old_status,
            new_status=complaint.status,
            changed_by=current_user.id,
            remarks=f"Complaint assigned to technician {technician.id}",
        )

        self.repository.create_history(history)

        self.db.flush()

        return complaint

    def update_status(
        self,
        complaint_id: int,
        data: ComplaintStatusUpdate,
        current_user: User,
    ) -> Complaint:

        complaint = self.get_complaint(
            complaint_id
        )

        if (
            data.status
            in {
                ComplaintStatus.IN_PROGRESS,
                ComplaintStatus.RESOLVED,
                ComplaintStatus.CLOSED,
            }
            and complaint.assigned_to is None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Complaint must be assigned before this status change",
            )

        if (
            data.status == ComplaintStatus.ASSIGNED
            and complaint.assigned_to is None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Complaint must have a technician assigned",
            )

        old_status = complaint.status

        complaint.status = data.status

        self.repository.update(complaint)

        history = ComplaintHistory(
            complaint_id=complaint.id,
            old_status=old_status,
            new_status=data.status,
            changed_by=current_user.id,
            remarks=data.remarks,
        )

        self.repository.create_history(history)

        self.db.flush()

        return complaint

    def list_complaints(
        self,
        customer_id: int | None = None,
        connection_id: int | None = None,
        complaint_type=None,
        priority=None,
        complaint_status=None,
        assigned_to: int | None = None,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):

        return self.repository.list_complaints(
            customer_id=customer_id,
            connection_id=connection_id,
            complaint_type=complaint_type,
            priority=priority,
            complaint_status=complaint_status,
            assigned_to=assigned_to,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def get_history(
        self,
        complaint_id: int,
    ) -> list[ComplaintHistory]:

        self.get_complaint(
            complaint_id
        )

        return self.repository.get_history(
            complaint_id
        )