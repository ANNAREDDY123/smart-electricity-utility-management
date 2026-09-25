from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.connection import ConnectionType
from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, db: Session):
        self.repository = CustomerRepository(db)

    def create_customer(
        self,
        data: CustomerCreate,
    ) -> Customer:

        existing_number = (
            self.repository.get_by_customer_number(
                data.customer_number
            )
        )

        if existing_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer number is already registered",
            )

        existing_email = self.repository.get_by_email(
            data.email
        )

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer email is already registered",
            )

        customer = Customer(
            customer_number=data.customer_number,
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            address=data.address,
            city=data.city,
        )

        return self.repository.create(customer)

    def get_customer(
        self,
        customer_id: int,
    ) -> Customer:

        customer = self.repository.get_by_id(
            customer_id
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        return customer

    def update_customer(
        self,
        customer_id: int,
        data: CustomerUpdate,
    ) -> Customer:

        customer = self.get_customer(customer_id)

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "email" in update_data:
            existing_email = (
                self.repository.get_by_email(
                    update_data["email"]
                )
            )

            if (
                existing_email
                and existing_email.id != customer.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Customer email is already registered",
                )

        for field, value in update_data.items():
            setattr(customer, field, value)

        return self.repository.update(customer)

    def delete_customer(
        self,
        customer_id: int,
    ) -> None:

        customer = self.get_customer(customer_id)

        self.repository.delete(customer)

    def list_customers(
        self,
        *,
        city=None,
        status=None,
        connection_type: ConnectionType | None = None,
        page=1,
        limit=20,
        sort_by="id",
        sort_order="asc",
    ):
        return self.repository.list_customers(
            city=city,
            status=status,
            connection_type=connection_type,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )