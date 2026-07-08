from dotenv import load_dotenv
import os

load_dotenv()

class Settings:

    def __init__(self):

        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER")

        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

        self.APP_TITLE = os.getenv("APP_TITLE", "Hospital RAG Assistant")

        self.APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

        self.DATABASE_URL = os.getenv("DATABASE_URL")

        self.REMINDER_DAYS = int(
            os.getenv("REMINDER_DAYS", 3)
        )

        self.CRON_TIME_HOUR = int(os.getenv("CRON_TIME_HOUR"))
        self.CRON_TIME_MINUTE = int(os.getenv("CRON_TIME_MINUTE"))

        self.SMTP_EMAIL = os.getenv("SMTP_EMAIL")
        self.SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
        self.SMTP_SERVER = os.getenv("SMTP_SERVER")
        self.SMTP_PORT = int(os.getenv("SMTP_PORT"))


settings = Settings()