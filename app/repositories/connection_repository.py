from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.connection import (
    Connection,
    ConnectionStatus,
    ConnectionType,
)


class ConnectionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        connection_id: int,
    ) -> Connection | None:
        return self.db.get(Connection, connection_id)

    def get_by_connection_number(
        self,
        connection_number: str,
    ) -> Connection | None:
        statement = select(Connection).where(
            Connection.connection_number == connection_number
        )
        return self.db.scalar(statement)

    def create(
        self,
        connection: Connection,
    ) -> Connection:
        self.db.add(connection)
        self.db.flush()
        self.db.refresh(connection)
        return connection

    def update(
        self,
        connection: Connection,
    ) -> Connection:
        self.db.flush()
        self.db.refresh(connection)
        return connection

    def list_connections(
        self,
        *,
        customer_id: int | None = None,
        connection_type: ConnectionType | None = None,
        tariff_type: str | None = None,
        status: ConnectionStatus | None = None,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "id",
        sort_order: str = "asc",
    ) -> tuple[list[Connection], int]:

        statement: Select = select(Connection)

        if customer_id is not None:
            statement = statement.where(
                Connection.customer_id == customer_id
            )

        if connection_type is not None:
            statement = statement.where(
                Connection.connection_type == connection_type
            )

        if tariff_type:
            statement = statement.where(
                Connection.tariff_type.ilike(
                    f"%{tariff_type}%"
                )
            )

        if status is not None:
            statement = statement.where(
                Connection.status == status
            )

        sort_column = getattr(
            Connection,
            sort_by,
            Connection.id,
        )

        if sort_order.lower() == "desc":
            statement = statement.order_by(
                sort_column.desc()
            )
        else:
            statement = statement.order_by(
                sort_column.asc()
            )

        all_matching = self.db.scalars(statement).all()

        total = len(all_matching)

        offset = (page - 1) * limit

        statement = statement.offset(offset).limit(limit)

        connections = self.db.scalars(statement).all()

        return connections, total