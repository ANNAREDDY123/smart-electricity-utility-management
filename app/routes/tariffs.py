from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tariff import TariffStatus
from app.schemas.tariff import (
    TariffApplyResponse,
    TariffCreate,
    TariffResponse,
    TariffUpdate,
)
from app.services.tariff_service import TariffService
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/tariffs",
    tags=["Tariffs"],
)


@router.post(
    "",
    response_model=TariffResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tariff(
    data: TariffCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Billing Officer",
        )
    ),
):
    service = TariffService(db)

    tariff = service.create_tariff(data)

    db.commit()
    db.refresh(tariff)

    return tariff


@router.get(
    "",
    response_model=list[TariffResponse],
)
def get_tariffs(
    connection_type: str | None = None,
    tariff_status: TariffStatus | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Billing Officer",
            "Customer Service Agent",
            "Customer",
        )
    ),
):
    service = TariffService(db)

    return service.list_tariffs(
        connection_type=connection_type,
        tariff_status=tariff_status,
    )


@router.put(
    "/{tariff_id}",
    response_model=TariffResponse,
)
def update_tariff(
    tariff_id: int,
    data: TariffUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Billing Officer",
        )
    ),
):
    service = TariffService(db)

    tariff = service.update_tariff(
        tariff_id,
        data,
    )

    db.commit()
    db.refresh(tariff)

    return tariff


@router.delete(
    "/{tariff_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tariff(
    tariff_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
        )
    ),
):
    service = TariffService(db)

    service.delete_tariff(tariff_id)

    db.commit()

    return None


@router.get(
    "/apply",
    response_model=TariffApplyResponse,
)
def apply_tariff(
    effective_date: date,
    connection_type: str = Query(
        min_length=1,
        max_length=30,
    ),
    units_consumed: Decimal = Query(
        ge=0,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Super Admin",
            "Billing Officer",
            "Customer Service Agent",
            "Customer",
        )
    ),
):
    service = TariffService(db)

    tariff = service.apply_tariff(
        connection_type=connection_type,
        units_consumed=units_consumed,
        effective_date=effective_date,
    )

    return {
        "tariff_id": tariff.id,
        "tariff_name": tariff.tariff_name,
        "connection_type": tariff.connection_type,
        "units_consumed": units_consumed,
        "rate_per_unit": tariff.rate_per_unit,
        "fixed_charge": tariff.fixed_charge,
        "effective_from": tariff.effective_from,
        "effective_to": tariff.effective_to,
    }