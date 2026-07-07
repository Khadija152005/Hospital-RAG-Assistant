from typing import List
from tools import log_notification
from schemas import EmailTask

class LoggerAgent:

    def log(
        self,
        email_tasks: list,         
        email_send_results: list    
    ) -> list:
        logger_results = []

       
        for email_task, send_result in zip(email_tasks, email_send_results):
            
           
            staff_id = email_task.assigned_staff.staff_id if email_task.assigned_staff else None
            recipient_email = email_task.assigned_staff.email if email_task.assigned_staff else None
            
            
            status_str = "SUCCESS" if send_result.success else "FAILED"
            error_msg = send_result.error if hasattr(send_result, 'error') else None

            log_res = log_notification(
                asset_id=email_task.asset_id,
                staff_id=staff_id,
                recipient_email=recipient_email,
                email_subject=email_task.email_subject,
                notification_type="MAINTENANCE_REMINDER",
                status=status_str,
                error_message=error_msg,
            )
            logger_results.append(log_res)

        return logger_results