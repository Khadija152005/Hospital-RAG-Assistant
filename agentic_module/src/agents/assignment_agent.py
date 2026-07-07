from tools import get_assignment_tool
from schemas import AssignmentResult, AssignedStaff
from typing import List


class AssignmentAgent:

    def enrich_tasks(self, tasks: dict) -> List[AssignmentResult]:

        enriched = []

        tasks_list = tasks.get("tasks", [])

        for task in tasks_list:

            staff = get_assignment_tool(task["asset_id"])

            if not staff:
                result = AssignmentResult(
                    asset_id=task["asset_id"],
                    asset_name=task["asset_name"],
                    department=task["department"],
                    next_maintenance_date=task.get("next_maintenance_date"),
                    assignment_status="UNASSIGNED",
                    assigned_staff=None
                )
            else:
                result = AssignmentResult(
                    asset_id=task["asset_id"],
                    asset_name=task["asset_name"],
                    department=task["department"],
                    next_maintenance_date=task.get("next_maintenance_date"),
                    assignment_status="ASSIGNED",
                    assigned_staff=AssignedStaff(**staff)
                )

            enriched.append(result)

        return enriched