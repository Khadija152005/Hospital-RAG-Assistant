from typing import List

from schemas import AssignmentResult, EmailTask


class EmailAgent:

    def build_emails(
        self,
        tasks: List[AssignmentResult],
    ) -> List[EmailTask]:

        emails: List[EmailTask] = []

        for task in tasks:

            if task.assigned_staff is None:
                continue

            email = EmailTask(
                asset_id=task.asset_id,
                asset_name=task.asset_name,
                department=task.department,
                next_maintenance_date=task.next_maintenance_date,
                assignment_status=task.assignment_status,
                assigned_staff=task.assigned_staff,
                email_subject=f"🚨 Maintenance Reminder - {task.asset_id}",
                email_body=self._build_body(task),
            )

            emails.append(email)

        return emails

    def _build_body(
        self,
        task: AssignmentResult,
    ) -> str:

        return f"""
Hello {task.assigned_staff.name},

This is a maintenance reminder for your assigned medical equipment.

Asset ID: {task.asset_id}
Asset Name: {task.asset_name}
Department: {task.department}

Next Maintenance Date: {task.next_maintenance_date}

Please ensure maintenance is completed before the scheduled date.

— Hospital Maintenance System
"""