from sqlalchemy.orm import Session

from models import NotificationLog
from schemas import NotificationLogCreate


class NotificationLogService:

    def __init__(self, db: Session):
        self.db = db

    def create_log(
        self,
        log_data: NotificationLogCreate
    ) -> NotificationLog:

        log = NotificationLog(
            **log_data.model_dump()
        )

        self.db.add(log)

        self.db.commit()

        self.db.refresh(log)

        return log