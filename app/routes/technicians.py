from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.technician import TechnicianAvailability
from app.schemas.technician import (
    TechnicianAvailabilityUpdate,
    TechnicianCreate,
    TechnicianResponse,
)
from app.services.technician_service import TechnicianService
from app.utils.dependencies import (
    get_current_active_user,
    require_roles,
)


router = APIRouter(
    prefix="/technicians",
    tags=["Technicians"],
)


@router.post(
    "",
    response_model=TechnicianResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_technician(
    data: TechnicianCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Customer Service Agent",
        )
    ),
):
    service = TechnicianService(db)

    technician = service.create_technician(data)

    db.commit()
    db.refresh(technician)

    return technician


@router.get(
    "",
    response_model=list[TechnicianResponse],
)
def get_technicians(
    availability_status: TechnicianAvailability | None = Query(
        default=None
    ),
    specialization: str | None = Query(
        default=None,
        min_length=2,
        max_length=100,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = TechnicianService(db)

    return service.list_technicians(
        availability_status=availability_status,
        specialization=specialization,
    )


@router.get(
    "/{technician_id}",
    response_model=TechnicianResponse,
)
def get_technician(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = TechnicianService(db)

    return service.get_technician(technician_id)


@router.put(
    "/{technician_id}/availability",
    response_model=TechnicianResponse,
)
def update_technician_availability(
    technician_id: int,
    data: TechnicianAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Customer Service Agent",
        )
    ),
):
    service = TechnicianService(db)

    technician = service.update_availability(
        technician_id=technician_id,
        data=data,
    )

    db.commit()
    db.refresh(technician)

    return technician