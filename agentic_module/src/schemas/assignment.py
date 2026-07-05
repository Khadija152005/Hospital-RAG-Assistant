from pydantic import BaseModel


class AssignedStaff(BaseModel):

    staff_id: str
    name: str
    email: str
    role: str


class AssignmentResult(BaseModel):

    asset_id: str
    assignment_status: str
    assigned_staff: AssignedStaff | None