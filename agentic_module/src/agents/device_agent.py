from tools import get_due_assets_tool


class DeviceAgent:

    def __init__(self):
        pass

    def run(self):
        """
        1. Get due assets
        2. Transform them into "agent decisions"
        """
        
        assets = get_due_assets_tool()
        
        if not assets:
            return {
                "status": "no_due_assets",
                "message": "No assets need maintenance right now"
            }

        tasks = []
        
        for asset in assets:
            
            task = {
                "asset_id": asset["asset_id"],
                "asset_name": asset["asset_name"],
                "department": asset["department"],
                "next_maintenance_date": asset["next_maintenance_date"],
                "priority": self._calculate_priority(asset),
                "action": "SEND_REMINDER_EMAIL"
            }

            tasks.append(task)
        
        return {
            "status": "success",
            "count": len(tasks),
            "tasks": tasks
        }

    def _calculate_priority(self, asset):
        """
        Simple rule-based logic for now
        (later we upgrade it to AI reasoning)
        """

        
        if str(asset["next_maintenance_date"]) < "2026-03-01":
            return "HIGH"

        return "MEDIUM"