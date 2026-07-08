from agents import (
    DeviceAgent,
    AssignmentAgent,
    EmailAgent,
    LoggerAgent
)

from tools import EmailSender


class CoordinatorAgent:

    def __init__(self):

        self.device_agent = DeviceAgent()

        self.assignment_agent = AssignmentAgent()

        self.email_agent = EmailAgent()

        self.email_sender = EmailSender()

        self.logger_agent = LoggerAgent()

    def run(self):

        # print("🚀 Starting Maintenance Workflow...")

        device_tasks = self.device_agent.run()

        # print("✅ Device tasks fetched successfully.")

        assignment_tasks = self.assignment_agent.enrich_tasks(device_tasks)

        # print("✅ Assignment tasks enriched successfully.")

        email_tasks = self.email_agent.build_emails(assignment_tasks)

        # print("✅ Email tasks built successfully.")

        email_send_results = self.email_sender.send_emails(email_tasks)

        # print("✅ Email Send Results")

        logger_results = self.logger_agent.log(email_tasks, email_send_results)
       
        # print("✅ Logger Results")

        
        return {
            "status": "success",
            "devices_found": len(device_tasks),
            "emails_generated": len(email_tasks),
            "emails_sent": sum(r.success for r in email_send_results),
            "notifications_logged": len(logger_results),
        }
