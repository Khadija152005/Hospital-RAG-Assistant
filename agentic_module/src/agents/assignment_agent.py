from tools import get_assignment_tool
from schemas import AssignmentResult, AssignedStaff
from typing import List


class AssignmentAgent:

    def enrich_tasks(self, tasks: list):

        enriched = []

        for task in tasks:

            staff = get_assignment_tool(task["asset_id"])

            if not staff:
                result = AssignmentResult(
                    asset_id=task["asset_id"],
                    assignment_status="UNASSIGNED",
                    assigned_staff=None
                )
            else:
                result = AssignmentResult(
                    asset_id=task["asset_id"],
                    assignment_status="ASSIGNED",
                    assigned_staff=AssignedStaff(**staff)
                )

            enriched.append(result)

        return enriched