from sqlalchemy.orm import Session

from app.repositories.audit_log_repository import AuditLogRepository


class AuditLogService:
    def __init__(self, db: Session):
        self.repository = AuditLogRepository(db)

    def log(
        self,
        *,
        user_id: int | None,
        action: str,
        resource: str,
        resource_id: int | None = None,
        details: str | None = None,
    ):
        return self.repository.create(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
        )