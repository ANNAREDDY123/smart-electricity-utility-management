from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.connection import Connection
from app.models.customer import Customer, CustomerStatus
from app.models.service_request import (
    ServiceRequest,
    ServiceRequestStatus,
)
from app.repositories.service_request_repository import (
    ServiceRequestRepository,
)
from app.schemas.service_request import ServiceRequestCreate


class ServiceRequestService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ServiceRequestRepository(db)

    def get_request(
        self,
        service_request_id: int,
    ) -> ServiceRequest:
        service_request = self.repository.get_by_id(
            service_request_id
        )

        if not service_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service request not found",
            )

        return service_request

    def _validate_customer(
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

        if customer.status == CustomerStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Suspended customers cannot create service requests",
            )

        if customer.status == CustomerStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Closed customers cannot create service requests",
            )

        return customer

    def _validate_connection(
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

    def create_request(
        self,
        data: ServiceRequestCreate,
    ) -> ServiceRequest:
        customer = self._validate_customer(
            data.customer_id
        )

        if (
            data.request_type.value == "New Connection"
            and data.connection_id is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="New Connection requests should not include a connection_id",
            )

        if data.connection_id is not None:
            connection = self._validate_connection(
                data.connection_id
            )

            if connection.customer_id != customer.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Connection does not belong to the customer",
                )

        service_request = ServiceRequest(
            customer_id=data.customer_id,
            connection_id=data.connection_id,
            request_type=data.request_type,
            description=data.description,
            requested_date=data.requested_date,
            status=ServiceRequestStatus.SUBMITTED,
        )

        service_request = self.repository.create(
            service_request
        )

        self.db.flush()

        return service_request

    def list_requests(
        self,
        customer_id: int | None = None,
        connection_id: int | None = None,
        request_type=None,
        request_status=None,
    ) -> list[ServiceRequest]:
        return self.repository.list_requests(
            customer_id=customer_id,
            connection_id=connection_id,
            request_type=request_type,
            request_status=request_status,
        )

    def approve_request(
        self,
        service_request_id: int,
    ) -> ServiceRequest:
        service_request = self.get_request(
            service_request_id
        )

        if service_request.status not in (
            ServiceRequestStatus.SUBMITTED,
            ServiceRequestStatus.UNDER_REVIEW,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only submitted or under-review requests can be approved",
            )

        service_request.status = ServiceRequestStatus.APPROVED

        service_request = self.repository.update(
            service_request
        )

        self.db.flush()

        return service_request

    def reject_request(
        self,
        service_request_id: int,
    ) -> ServiceRequest:
        service_request = self.get_request(
            service_request_id
        )

        if service_request.status not in (
            ServiceRequestStatus.SUBMITTED,
            ServiceRequestStatus.UNDER_REVIEW,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only submitted or under-review requests can be rejected",
            )

        service_request.status = ServiceRequestStatus.REJECTED

        service_request = self.repository.update(
            service_request
        )

        self.db.flush()

        return service_request

    def complete_request(
        self,
        service_request_id: int,
    ) -> ServiceRequest:
        service_request = self.get_request(
            service_request_id
        )

        if service_request.status != ServiceRequestStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only approved requests can be completed",
            )

        service_request.status = ServiceRequestStatus.COMPLETED

        service_request = self.repository.update(
            service_request
        )

        self.db.flush()

        return service_request