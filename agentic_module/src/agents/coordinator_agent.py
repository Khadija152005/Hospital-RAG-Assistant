from agents import (
    DeviceAgent,
    AssignmentAgent,
    EmailAgent,
    LoggerAgent
)

from tools import EmailSender

from schemas import MaintenanceWorkflowState


class CoordinatorAgent:

    def __init__(self):

        self.device_agent = DeviceAgent()

        self.assignment_agent = AssignmentAgent()

        self.email_agent = EmailAgent()

        self.email_sender = EmailSender()

        self.logger_agent = LoggerAgent()

    def run(self):

        state = MaintenanceWorkflowState()


        # 1. Device Agent

        state.devices = self.device_agent.run()


        # 2. Assignment Agent

        state.assignments = self.assignment_agent.enrich_tasks(
            state.devices
        )


        # 3. Email Agent

        state.emails = self.email_agent.build_emails(
            state.assignments
        )

        # for email in state.emails[:1]:
        #     print(email.email_body)

        # 4. Email Sender Tool

        state.email_results = self.email_sender.send_emails(
            state.emails
        )


        # 5. Logger Agent

        state.logs = self.logger_agent.log(
            state.emails,
            state.email_results,
        )


        return {
            "status": "success",
            "devices_found": len(state.devices),
            "emails_generated": len(state.emails),
            "emails_sent": sum(
                r.success for r in state.email_results
            ),
            "notifications_logged": len(state.logs),
        }
