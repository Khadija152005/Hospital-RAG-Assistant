from pydantic import BaseModel

from datetime import date
from typing import Optional

from schemas import AssignedStaff


class EmailTask(BaseModel):

    asset_id: str

    asset_name: str

    department: str

    next_maintenance_date: date

    assignment_status: str

    assigned_staff: Optional[AssignedStaff] = None

    email_subject: str

    email_body: str