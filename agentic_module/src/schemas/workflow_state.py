from typing import List

from pydantic import BaseModel

from schemas import (
    DueAsset,
    AssignmentResult,
    EmailTask,
    EmailResult,
)


class MaintenanceWorkflowState(BaseModel):

    devices: List[DueAsset] = []

    assignments: List[AssignmentResult] = []

    emails: List[EmailTask] = []

    email_results: List[EmailResult] = []

    logs: list = []