from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserStatusUpdate
from app.services.user_service import UserService
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/users",
    tags=["User Management"],
)


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
)
def update_user_status(
    user_id: int,
    data: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.SUPER_ADMIN)
    ),
):
    service = UserService(db)

    user = service.update_activation_status(
        target_user_id=user_id,
        is_active=data.is_active,
    )

    db.commit()

    return user