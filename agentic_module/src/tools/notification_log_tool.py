from sqlalchemy import (
    Column,
    Integer,
    Text,
    TIMESTAMP,
    ForeignKey,
    func,
)

from db import Base


class NotificationLog(Base):

    __tablename__ = "notification_log"

    notification_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    asset_id = Column(
        Text,
        ForeignKey("asset.asset_id"),
        nullable=False,
    )

    staff_id = Column(
        Text,
        ForeignKey("staff.staff_id"),
        nullable=False,
    )

    recipient_email = Column(Text)

    email_subject = Column(Text)

    notification_type = Column(
        Text,
        nullable=False,
    )

    status = Column(
        Text,
        nullable=False,
    )

    sent_at = Column(
        TIMESTAMP,
        server_default=func.now(),
    )

    error_message = Column(Text)