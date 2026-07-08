from agents import (
    DeviceAgent,
    AssignmentAgent,
    EmailAgent,
    LoggerAgent,
)


# from agents.device_agent import DeviceAgent
# from agents.assignment_agent import AssignmentAgent
# from agents.email_agent import EmailAgent
# from agents.logger_agent import LoggerAgent

from tools import EmailSender


def device_node(state):

    agent = DeviceAgent()

    return {
        "devices": agent.run()
    }



def assignment_node(state):

    agent = AssignmentAgent()

    return {
        "assignments": agent.enrich_tasks(
            state["devices"]
        )
    }



def email_node(state):

    agent = EmailAgent()

    return {
        "emails": agent.build_emails(
            state["assignments"]
        )
    }



def sender_node(state):

    sender = EmailSender()

    return {
        "email_results": sender.send_emails(
            state["emails"]
        )
    }



def logger_node(state):

    agent = LoggerAgent()

    return {
        "logs": agent.log(
            state["emails"],
            state["email_results"],
        )
    }