from db import SessionLocal

from schemas import NotificationLogCreate
from services import NotificationLogService


def log_notification(
    asset_id: str,
    staff_id: str,
    recipient_email: str,
    email_subject: str,
    notification_type: str,
    status: str,
    error_message: str | None = None,
):

    db = SessionLocal()

    try:

        service = NotificationLogService(db)

        log = NotificationLogCreate(
            asset_id=asset_id,
            staff_id=staff_id,
            recipient_email=recipient_email,
            email_subject=email_subject,
            notification_type=notification_type,
            status=status,
            error_message=error_message,
        )

        return service.create_log(log)

    finally:
        db.close()