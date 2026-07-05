from typing import List
from schemas import AssignmentResult


class EmailAgent:

    def build_emails(self, tasks: List[AssignmentResult]):

        emails = []

        for task in tasks:

            if not task.assigned_staff:
                continue

            email = {
                "to": task.assigned_staff.email,
                "subject": f"🚨 Maintenance Reminder - {task.asset_id}",
                "body": self._build_body(task)
            }

            emails.append(email)

        return emails

    def _build_body(self, task: AssignmentResult):

        return f"""
Hello {task.assigned_staff.name},

This is a maintenance reminder for your assigned medical equipment.

Asset ID: {task.asset_id}
Department: {task.assigned_staff.role}
Status: {task.assignment_status}

Please ensure maintenance is completed as scheduled.

— Hospital Maintenance System
"""