from pydantic import BaseModel
from datetime import date
from typing import Optional


class AssignedStaff(BaseModel):

    staff_id: str
    name: str
    email: str
    role: str


class AssignmentResult(BaseModel):

    asset_id: str
    asset_name: str
    department: str
    next_maintenance_date: Optional[date] = None
    assignment_status: str
    assigned_staff: AssignedStaff | None