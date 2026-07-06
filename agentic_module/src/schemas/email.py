from pydantic import BaseModel


class EmailResult(BaseModel):
    success: bool
    error: str | None = None