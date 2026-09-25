from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        user_id: int | None,
        action: str,
        resource: str,
        resource_id: int | None = None,
        details: str | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
        )

        self.db.add(audit_log)
        self.db.flush()
        self.db.refresh(audit_log)

        return audit_log