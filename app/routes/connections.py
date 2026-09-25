from datetime import date
from math import ceil

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.connection import (
    ConnectionStatus,
    ConnectionType,
)
from app.models.user import User, UserRole
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionResponse,
    ConnectionUpdate,
)
from app.schemas.pagination import PaginationResponse
from app.services.connection_service import ConnectionService
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/connections",
    tags=["Service Connections"],
)


@router.post(
    "",
    response_model=ConnectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_connection(
    data: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.CUSTOMER_SERVICE_AGENT,
        )
    ),
):
    service = ConnectionService(db)

    connection = service.create_connection(data)

    db.commit()

    return connection


@router.get(
    "",
    response_model=PaginationResponse[ConnectionResponse],
)
def list_connections(
    customer_id: int | None = Query(
        default=None,
        ge=1,
    ),
    connection_type: ConnectionType | None = Query(
        default=None,
    ),
    tariff_type: str | None = Query(
        default=None,
    ),
    status_filter: ConnectionStatus | None = Query(
        default=None,
        alias="status",
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
            UserRole.FIELD_TECHNICIAN,
        )
    ),
):
    service = ConnectionService(db)

    connections, total = service.list_connections(
        customer_id=customer_id,
        connection_type=connection_type,
        tariff_type=tariff_type,
        status=status_filter,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    pages = ceil(total / limit) if total else 0

    return {
        "items": connections,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get(
    "/{connection_id}",
    response_model=ConnectionResponse,
)
def get_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.CUSTOMER_SERVICE_AGENT,
            UserRole.BILLING_OFFICER,
            UserRole.FIELD_TECHNICIAN,
            UserRole.CUSTOMER,
        )
    ),
):
    service = ConnectionService(db)

    return service.get_connection(connection_id)


@router.put(
    "/{connection_id}",
    response_model=ConnectionResponse,
)
def update_connection(
    connection_id: int,
    data: ConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.CUSTOMER_SERVICE_AGENT,
        )
    ),
):
    service = ConnectionService(db)

    connection = service.update_connection(
        connection_id,
        data,
    )

    db.commit()

    return connection


@router.patch(
    "/{connection_id}/disconnect",
    response_model=ConnectionResponse,
)
def disconnect_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.CUSTOMER_SERVICE_AGENT,
        )
    ),
):
    service = ConnectionService(db)

    connection = service.disconnect_connection(
        connection_id
    )

    db.commit()

    return connection