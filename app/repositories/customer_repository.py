from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.connection import Connection, ConnectionType
from app.models.customer import Customer, CustomerStatus


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, customer_id: int) -> Customer | None:
        statement = select(Customer).where(
            Customer.id == customer_id,
            Customer.is_deleted.is_(False),
        )
        return self.db.scalar(statement)

    def get_by_customer_number(
        self,
        customer_number: str,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.customer_number == customer_number,
            Customer.is_deleted.is_(False),
        )

        return self.db.scalar(statement)

    def get_by_email(
        self,
        email: str,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.email == email,
            Customer.is_deleted.is_(False),
        )

        return self.db.scalar(statement)

    def create(
        self,
        customer: Customer,
    ) -> Customer:
        self.db.add(customer)
        self.db.flush()
        self.db.refresh(customer)

        return customer

    def update(
        self,
        customer: Customer,
    ) -> Customer:
        self.db.flush()
        self.db.refresh(customer)

        return customer

    def delete(
        self,
        customer: Customer,
    ) -> None:
        customer.is_deleted = True
        customer.status = CustomerStatus.CLOSED
        self.db.add(customer)
        self.db.flush()

    def list_customers(
        self,
        *,
        city: str | None = None,
        status: CustomerStatus | None = None,
        connection_type: ConnectionType | None = None,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "id",
        sort_order: str = "asc",
    ) -> tuple[list[Customer], int]:

        statement: Select = select(Customer).where(
            Customer.is_deleted.is_(False)
        )

        if connection_type is not None:
            statement = statement.join(
                Connection,
                Connection.customer_id == Customer.id,
            )

        if city:
            statement = statement.where(
                Customer.city.ilike(f"%{city}%")
            )

        if status:
            statement = statement.where(
                Customer.status == status
            )

        if connection_type is not None:
            statement = statement.where(
                Connection.connection_type == connection_type
            )

        sort_columns = {
            "id": Customer.id,
            "customer_number": Customer.customer_number,
            "full_name": Customer.full_name,
            "email": Customer.email,
            "city": Customer.city,
            "status": Customer.status,
        }

        sort_column = sort_columns.get(
            sort_by,
            Customer.id,
        )

        if sort_order.lower() == "desc":
            statement = statement.order_by(
                sort_column.desc()
            )
        else:
            statement = statement.order_by(
                sort_column.asc()
            )

        all_customers = list(
            self.db.scalars(statement).unique().all()
        )

        total = len(all_customers)

        offset = (page - 1) * limit

        customers = list(
            self.db.scalars(
                statement.offset(offset).limit(limit)
            ).unique().all()
        )

        return customers, total