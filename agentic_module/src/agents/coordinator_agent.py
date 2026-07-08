from graph.maintenance_graph import maintenance_graph


class CoordinatorAgent:

    def run(self):

        result = maintenance_graph.invoke(
            {
                "devices": {},
                "assignments": [],
                "emails": [],
                "email_results": [],
                "logs": [],
            }
        )

        return {
            "status": "success",
            "devices_found": result["devices"]["count"],
            "emails_generated": len(result["emails"]),
            "emails_sent": sum(
                r.success for r in result["email_results"]
            ),
            "notifications_logged": len(result["logs"]),
        }