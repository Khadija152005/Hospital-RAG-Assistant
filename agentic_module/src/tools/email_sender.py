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

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str
    ) -> EmailResult:

        msg = MIMEMultipart()
        msg["From"] = self.smtp_email
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP(
                self.smtp_server,
                self.smtp_port
            )

            server.starttls()
            server.login(self.smtp_email, self.smtp_password)
            server.send_message(msg)
            server.quit()

            return EmailResult(success=True)

        except Exception as e:
            return EmailResult(
                success=False,
                error=str(e)
            )