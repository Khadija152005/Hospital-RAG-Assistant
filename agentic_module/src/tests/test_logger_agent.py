# to run test
# python -m tests.test_logger_agent 
# then go to neon and run this query to see the log entry

# SELECT *
# FROM notification_log
# ORDER BY notification_id DESC;

from agents import LoggerAgent
from schemas import EmailTask, AssignedStaff
from datetime import date


def test_logger_agent():

    logger = LoggerAgent()

    staff = AssignedStaff(
        staff_id="ENG001",
        name="Ahmed",
        email="test@test.com",
        role="Engineer"
    )

    email_task = EmailTask(
        asset_id="MRI-001",
        asset_name="MRI Scanner",
        department="Radiology",
        next_maintenance_date=date.today(),
        assignment_status="ASSIGNED",
        assigned_staff=staff,
        email_subject="Test Email",
        email_body="Test Body"
    )

    result = logger.log(
        email_task=email_task,
        status="SUCCESS"
    )

    print("\nLogger Result:")
    print(result)


if __name__ == "__main__":
    test_logger_agent()