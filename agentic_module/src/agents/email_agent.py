from typing import List

from schemas import AssignmentResult, EmailTask
from tools import LLMTool


class EmailAgent:

    def __init__(self):

        self.llm_tool = LLMTool()


    def build_emails(
        self,
        tasks: List[AssignmentResult],
    ) -> List[EmailTask]:

        emails: List[EmailTask] = []

        for task in tasks:

            if task.assigned_staff is None:
                continue


            email_body = self.llm_tool.generate(
                self._build_prompt(task)
            )


            email = EmailTask(
                asset_id=task.asset_id,
                asset_name=task.asset_name,
                department=task.department,
                next_maintenance_date=task.next_maintenance_date,
                assignment_status=task.assignment_status,
                assigned_staff=task.assigned_staff,

                email_subject=f"🚨 Maintenance Reminder - {task.asset_id}",

                email_body=email_body,
            )


            emails.append(email)

        return emails


    def _build_prompt(
        self,
        task: AssignmentResult,
    ) -> str:

        return f"""
You are a professional hospital maintenance assistant.

Your task is to write ONLY the email body for a maintenance reminder.

Do not include:
- Email subject
- Explanations
- Additional comments
- Placeholders such as [Your Name], [Hospital Name], or [Contact Information]

Recipient:
Name: {task.assigned_staff.name}
Role: {task.assigned_staff.role}

Equipment information:
Asset ID: {task.asset_id}
Asset Name: {task.asset_name}
Department: {task.department}

Scheduled maintenance date:
{task.next_maintenance_date}

Instructions:
- Start the email with a professional greeting using the recipient's name.
- Keep the email concise and professional.
- Mention the equipment details and asset ID.
- Mention the scheduled maintenance date.
- Request completing the maintenance before the scheduled date.
- Use only the provided information.
- End with a professional closing.
- Write the email in English only.
- Do not translate the recipient's name.
"""