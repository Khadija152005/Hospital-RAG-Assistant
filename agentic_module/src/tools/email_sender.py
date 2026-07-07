import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core import settings
from schemas.email import EmailResult


class EmailSender:

    def __init__(self):
        self.smtp_email = settings.SMTP_EMAIL
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT

    def send_emails(
        self,
        email_tasks: list
    ) -> list[EmailResult]:
        
        results = []
        
        if not email_tasks:
            return results

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_email, self.smtp_password)

            for task in email_tasks:
                if not task.assigned_staff or not task.assigned_staff.email:
                    print(f"⚠️ Skipping Asset {task.asset_id}: No staff or email assigned.")
                    results.append(EmailResult(success=False, error="No staff assigned"))
                    continue

                msg = MIMEMultipart()
                msg["From"] = self.smtp_email
                msg["To"] = task.assigned_staff.email
                msg["Subject"] = task.email_subject
                msg.attach(MIMEText(task.email_body, "plain"))

                try:
                    server.send_message(msg)
                    print(f"✅ Email sent successfully to {task.assigned_staff.email}")
                    results.append(EmailResult(success=True))
                except Exception as send_error:
                    print(f"❌ Failed to send email to {task.assigned_staff.email}: {send_error}")
                    results.append(EmailResult(success=False, error=str(send_error)))

            server.quit()

        except Exception as connection_error:
            print(f"🚨 SMTP Connection Error: {connection_error}")
            return [EmailResult(success=False, error=f"Connection failed: {connection_error}")] * len(email_tasks)

        return results