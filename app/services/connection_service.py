from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.connection import (
    Connection,
    ConnectionStatus,
)
from app.repositories.connection_repository import (
    ConnectionRepository,
)
from app.repositories.customer_repository import (
    CustomerRepository,
)
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionUpdate,
)


class ConnectionService:
    def __init__(self, db: Session):
        self.repository = ConnectionRepository(db)
        self.customer_repository = CustomerRepository(db)

    def create_connection(
        self,
        data: ConnectionCreate,
    ) -> Connection:

        customer = self.customer_repository.get_by_id(
            data.customer_id
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        if customer.status.value == "Closed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Closed customers cannot create connections",
            )

        existing = self.repository.get_by_connection_number(
            data.connection_number
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Connection number is already registered",
            )

        connection = Connection(
            customer_id=data.customer_id,
            connection_number=data.connection_number,
            connection_type=data.connection_type,
            sanctioned_load=data.sanctioned_load,
            tariff_type=data.tariff_type,
            connection_date=data.connection_date,
            status=data.status,
        )

        return self.repository.create(connection)

    def get_connection(
        self,
        connection_id: int,
    ) -> Connection:

        connection = self.repository.get_by_id(
            connection_id
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        return connection

    def update_connection(
        self,
        connection_id: int,
        data: ConnectionUpdate,
    ) -> Connection:

        connection = self.get_connection(connection_id)

        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(connection, field, value)

        return self.repository.update(connection)

    def disconnect_connection(
        self,
        connection_id: int,
    ) -> Connection:

        connection = self.get_connection(connection_id)

        if connection.status == ConnectionStatus.DISCONNECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Connection is already disconnected",
            )

        connection.status = ConnectionStatus.DISCONNECTED

        return self.repository.update(connection)

    def ensure_bill_generation_allowed(
        self,
        connection_id: int,
    ) -> Connection:

        connection = self.get_connection(connection_id)

        if connection.status == ConnectionStatus.DISCONNECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Disconnected connections cannot generate new bills",
            )

        return connection

    def list_connections(
        self,
        *,
        customer_id=None,
        connection_type=None,
        tariff_type=None,
        status=None,
        page=1,
        limit=20,
        sort_by="id",
        sort_order="asc",
    ):
        return self.repository.list_connections(
            customer_id=customer_id,
            connection_type=connection_type,
            tariff_type=tariff_type,
            status=status,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )