from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.service_request import (
    ServiceRequest,
    ServiceRequestStatus,
)


class ServiceRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        service_request_id: int,
    ) -> ServiceRequest | None:
        return self.db.get(
            ServiceRequest,
            service_request_id,
        )

    def list_requests(
        self,
        customer_id: int | None = None,
        connection_id: int | None = None,
        request_type=None,
        request_status=None,
    ) -> list[ServiceRequest]:
        query = select(ServiceRequest)

        if customer_id is not None:
            query = query.where(
                ServiceRequest.customer_id == customer_id
            )

        if connection_id is not None:
            query = query.where(
                ServiceRequest.connection_id == connection_id
            )

        if request_type is not None:
            query = query.where(
                ServiceRequest.request_type == request_type
            )

        if request_status is not None:
            query = query.where(
                ServiceRequest.status == request_status
            )

        query = query.order_by(
            ServiceRequest.requested_date.desc(),
            ServiceRequest.id.desc(),
        )

        return list(self.db.scalars(query).all())

    def create(
        self,
        service_request: ServiceRequest,
    ) -> ServiceRequest:
        self.db.add(service_request)
        self.db.flush()
        self.db.refresh(service_request)
        return service_request

    def update(
        self,
        service_request: ServiceRequest,
    ) -> ServiceRequest:
        self.db.flush()
        self.db.refresh(service_request)
        return service_request