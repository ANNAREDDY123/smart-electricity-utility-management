from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.complaint import (
    Complaint,
    ComplaintHistory,
)


class ComplaintRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        complaint_id: int,
    ) -> Complaint | None:
        return self.db.get(
            Complaint,
            complaint_id,
        )

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
    ) -> tuple[list[Complaint], int]:

        query = select(Complaint)

        if customer_id is not None:
            query = query.where(
                Complaint.customer_id == customer_id
            )

        if connection_id is not None:
            query = query.where(
                Complaint.connection_id == connection_id
            )

        if complaint_type is not None:
            query = query.where(
                Complaint.complaint_type
                == complaint_type
            )

        if priority is not None:
            query = query.where(
                Complaint.priority == priority
            )

        if complaint_status is not None:
            query = query.where(
                Complaint.status == complaint_status
            )

        if assigned_to is not None:
            query = query.where(
                Complaint.assigned_to == assigned_to
            )

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        total = self.db.scalar(count_query) or 0

        sort_columns = {
            "id": Complaint.id,
            "created_at": Complaint.created_at,
            "updated_at": Complaint.updated_at,
            "priority": Complaint.priority,
            "status": Complaint.status,
            "complaint_type": Complaint.complaint_type,
            "assigned_to": Complaint.assigned_to,
        }

        sort_column = sort_columns.get(
            sort_by,
            Complaint.created_at,
        )

        if sort_order.lower() == "asc":
            query = query.order_by(
                asc(sort_column),
                asc(Complaint.id),
            )
        else:
            query = query.order_by(
                desc(sort_column),
                desc(Complaint.id),
            )

        offset = (page - 1) * limit

        query = query.offset(offset).limit(limit)

        complaints = list(
            self.db.scalars(query).all()
        )

        return complaints, total

    def create(
        self,
        complaint: Complaint,
    ) -> Complaint:
        self.db.add(complaint)
        self.db.flush()
        self.db.refresh(complaint)

        return complaint

    def update(
        self,
        complaint: Complaint,
    ) -> Complaint:
        self.db.flush()
        self.db.refresh(complaint)

        return complaint

    def create_history(
        self,
        history: ComplaintHistory,
    ) -> ComplaintHistory:
        self.db.add(history)
        self.db.flush()
        self.db.refresh(history)

        return history

    def get_history(
        self,
        complaint_id: int,
    ) -> list[ComplaintHistory]:

        query = (
            select(ComplaintHistory)
            .where(
                ComplaintHistory.complaint_id
                == complaint_id
            )
            .order_by(
                ComplaintHistory.changed_at.asc(),
                ComplaintHistory.id.asc(),
            )
        )

        return list(
            self.db.scalars(query).all()
        )