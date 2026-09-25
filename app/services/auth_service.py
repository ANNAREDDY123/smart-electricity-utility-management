from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    UserLogin,
    UserRegister,
)
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def register(self, data: UserRegister) -> User:
        existing_user = self.user_repository.get_by_email(data.email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

        user = User(
            full_name=data.full_name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role,
            is_active=True,
        )

        return self.user_repository.create(user)

    def login(self, data: UserLogin) -> dict:
        user = self.user_repository.get_by_email(data.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        access_token = create_access_token(
            user_id=user.id,
            role=user.role.value,
        )

        refresh_token = create_refresh_token(
            user_id=user.id,
            role=user.role.value,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def get_current_user(self, user_id: int) -> User:
        user = self.user_repository.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    def change_password(
        self,
        user: User,
        data: ChangePasswordRequest,
    ) -> None:

        if not verify_password(
            data.current_password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        if data.current_password == data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password",
            )

        user.password_hash = hash_password(data.new_password)

        self.user_repository.update(user)