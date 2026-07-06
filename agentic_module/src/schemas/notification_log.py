from pydantic import BaseModel
from datetime import date
from typing import Optional


class NotificationLogCreate(BaseModel):

    asset_id: str

    staff_id: str

    recipient_email: str

    email_subject: str

    notification_type: str

    status: str

    error_message: Optional[str] = None