from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def update_activation_status(
        self,
        target_user_id: int,
        is_active: bool,
    ) -> User:
        user = self.user_repository.get_by_id(target_user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.is_active = is_active

        return self.user_repository.update(user)