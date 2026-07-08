from conversational_analytics.app.template_router import route_question


def test_template_router_matches_total_count_icu() -> None:
    q = "What is the total count of our ICU assets?"
    res = route_question(q)
    assert res is not None
    assert res.sql.strip().lower().startswith("select")


def test_template_router_matches_highest_downtime() -> None:
    q = "Which medical device experiences the highest downtime?"
    res = route_question(q)
    assert res is not None
    assert "downtime" in res.sql.lower()


def test_template_router_matches_department_count_question() -> None:
    q = "How many assets are assigned to ER?"
    res = route_question(q)
    assert res is not None
    assert "asset_count" in res.sql.lower()
    assert "ER" in res.sql
