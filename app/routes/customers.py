from math import ceil

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.connection import ConnectionType
from app.models.customer import CustomerStatus
from app.models.user import User, UserRole
from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
)
from app.schemas.pagination import PaginationResponse
from app.services.customer_service import CustomerService
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.CUSTOMER_SERVICE_AGENT,
        )
    ),
):
    service = CustomerService(db)

    customer = service.create_customer(data)

    db.commit()

    return customer


@router.get(
    "",
    response_model=PaginationResponse[CustomerResponse],
)
def list_customers(
    city: str | None = Query(default=None),
    status_filter: CustomerStatus | None = Query(
        default=None,
        alias="status",
    ),
    connection_type: ConnectionType | None = Query(
        default=None,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    sort_by: str = Query(
        default="id",
    ),
    sort_order: str = Query(
        default="asc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.CUSTOMER_SERVICE_AGENT,
            UserRole.BILLING_OFFICER,
        )
    ),
):
    service = CustomerService(db)

    customers, total = service.list_customers(
        city=city,
        status=status_filter,
        connection_type=connection_type,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    pages = ceil(total / limit) if total else 0

    return {
        "items": customers,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.CUSTOMER_SERVICE_AGENT,
            UserRole.BILLING_OFFICER,
            UserRole.CUSTOMER,
        )
    ),
):
    service = CustomerService(db)

    return service.get_customer(customer_id)


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.CUSTOMER_SERVICE_AGENT,
        )
    ),
):
    service = CustomerService(db)

    customer = service.update_customer(
        customer_id,
        data,
    )

    db.commit()

    return customer


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.SUPER_ADMIN)
    ),
):
    service = CustomerService(db)

    service.delete_customer(customer_id)

    db.commit()

    return None