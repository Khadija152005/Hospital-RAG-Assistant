from agents import (
    DeviceAgent,
    AssignmentAgent,
    EmailAgent,
)

from tools import EmailSender


class CoordinatorAgent:

    def __init__(self):

        self.device_agent = DeviceAgent()

        self.assignment_agent = AssignmentAgent()

        self.email_agent = EmailAgent()

        self.email_sender = EmailSender()

    def run(self):

        print("🚀 Starting Maintenance Workflow...")

        device_result = self.device_agent.run()

        print("✅ Device Results")

        assignment_result = self.assignment_agent.enrich_tasks(device_result)

        print("✅ Assignment Results")

        email_result = self.email_agent.build_emails(assignment_result)

        print("✅ Email Results")

        print(email_result)