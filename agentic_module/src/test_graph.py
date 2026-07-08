from graph.maintenance_graph import maintenance_graph


result = maintenance_graph.invoke(
    {
        "devices": [],
        "assignments": [],
        "emails": [],
        "email_results": [],
        "logs": [],
    }
)


print(result)