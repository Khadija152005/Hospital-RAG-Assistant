from __future__ import annotations

import pytest

from conversational_analytics.app.sql_safety import UnsafeSqlError, validate_sql


def test_validate_sql_allows_simple_select() -> None:
    sql = "SELECT asset_id, asset_name FROM assets"
    assert validate_sql(sql) == sql


@pytest.mark.parametrize(
    ("sql"),
    [
        "INSERT INTO assets VALUES (1)",
        "UPDATE assets SET name = 'X'",
        "DELETE FROM assets",
        "DROP TABLE assets",
        "CREATE TABLE assets (id INT)",
        "SELECT * FROM assets; DROP TABLE users",
        "WITH sample AS (SELECT 1) SELECT * FROM sample",
    ],
)
def test_validate_sql_blocks_unsafe_statements(sql: str) -> None:
    with pytest.raises(UnsafeSqlError):
        validate_sql(sql)
