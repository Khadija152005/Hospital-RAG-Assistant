from langgraph.graph import StateGraph, END

from .state import MaintenanceGraphState

from .nodes import (
    device_node,
    assignment_node,
    email_node,
    sender_node,
    logger_node,
)


def build_maintenance_graph():

    workflow = StateGraph(
        MaintenanceGraphState
    )


    # Add Nodes

    workflow.add_node(
        "device",
        device_node
    )

    workflow.add_node(
        "assignment",
        assignment_node
    )

    workflow.add_node(
        "email",
        email_node
    )

    workflow.add_node(
        "sender",
        sender_node
    )

    workflow.add_node(
        "logger",
        logger_node
    )


    # Define Flow

    workflow.set_entry_point(
        "device"
    )


    workflow.add_edge(
        "device",
        "assignment"
    )

    workflow.add_edge(
        "assignment",
        "email"
    )

    workflow.add_edge(
        "email",
        "sender"
    )

    workflow.add_edge(
        "sender",
        "logger"
    )


    workflow.add_edge(
        "logger",
        END
    )


    return workflow.compile()



maintenance_graph = build_maintenance_graph()