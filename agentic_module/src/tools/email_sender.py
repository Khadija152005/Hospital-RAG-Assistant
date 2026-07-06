import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from core import Settings

load_dotenv()


class EmailSender:

    def __init__(self):
        self.smtp_email = Settings().SMTP_EMAIL
        self.smtp_password = Settings().SMTP_PASSWORD
        self.smtp_server = Settings().SMTP_SERVER
        self.smtp_port = Settings().SMTP_PORT

    def send_email(self, to_email: str, subject: str, body: str):

        msg = MIMEMultipart()
        msg["From"] = self.smtp_email
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_email, self.smtp_password)

            server.send_message(msg)
            server.quit()

            print(f"✅ Email sent to {to_email}")

        except Exception as e:
            print(f"❌ Failed to send email: {e}")