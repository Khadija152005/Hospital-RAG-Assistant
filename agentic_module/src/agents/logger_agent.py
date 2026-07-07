from tools import log_notification
from schemas import EmailTask


class LoggerAgent:


    def log(
        self,
        email_task: EmailTask,
        status: str,
        error_message: str | None = None,
    ):

        return log_notification(

            asset_id=email_task.asset_id,

            staff_id=email_task.assigned_staff.staff_id,

            recipient_email=email_task.assigned_staff.email,

            email_subject=email_task.email_subject,

            notification_type="MAINTENANCE_REMINDER",

            status=status,

            error_message=error_message,
        )