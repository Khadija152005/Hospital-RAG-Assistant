from __future__ import annotations

from fastapi.testclient import TestClient

from conversational_analytics.app.analytics_service import GeminiRateLimitError
from conversational_analytics.app.main import app, get_analytics_service
from conversational_analytics.app.sql_safety import UnsafeSqlError


class DummyService:
    def __init__(self, response: dict | None = None, exc: Exception | None = None) -> None:
        self.response = response or {
            "question": "Which medical device experiences the highest downtime?",
            "answer": "The Infusion Pump has the highest total downtime.",
            "status": "success",
            "sql_query": "SELECT a.asset_name, SUM(am.downtime_hours) AS total_downtime FROM asset_maintenance am JOIN asset a ON am.asset_id = a.asset_id GROUP BY a.asset_name ORDER BY total_downtime DESC LIMIT 1",
            "rows": [{"asset_name": "Infusion Pump", "total_downtime": 1440}],
        }
        self.exc = exc

    def ask_question(self, question: str) -> dict:
        if self.exc:
            raise self.exc
        return {**self.response, "question": question}


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "conversational-analytics"}


def test_ask_endpoint_returns_clean_response() -> None:
    app.dependency_overrides[get_analytics_service] = lambda: DummyService()
    response = client.post(
        "/ask",
        json={"question": "Which medical device experiences the highest downtime?"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["question"] == "Which medical device experiences the highest downtime?"
    assert payload["answer"]
    assert payload["sql_query"].startswith("SELECT")
    assert payload["rows"][0]["asset_name"] == "Infusion Pump"


def test_rate_limit_exception_maps_to_429() -> None:
    app.dependency_overrides[get_analytics_service] = lambda: DummyService(exc=GeminiRateLimitError("rate limited"))
    response = client.post("/ask", json={"question": "Top 5 assets by downtime"})
    app.dependency_overrides.clear()

    assert response.status_code == 429
    assert response.json()["detail"] == "The analytics service is temporarily rate-limited. Please retry shortly."


def test_unsafe_sql_exception_maps_to_400() -> None:
    app.dependency_overrides[get_analytics_service] = lambda: DummyService(exc=UnsafeSqlError("Unsafe SQL operation detected and blocked."))
    response = client.post("/ask", json={"question": "Drop the table"})
    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsafe SQL operation detected and blocked."
