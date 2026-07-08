from typing import TypedDict, List

from schemas import (
    DueAsset,
    AssignmentResult,
    EmailTask,
    EmailResult,
)


class MaintenanceGraphState(TypedDict):

    devices: dict

    assignments: List[AssignmentResult]

    emails: List[EmailTask]

    email_results: List[EmailResult]

    logs: list