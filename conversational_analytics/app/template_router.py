from __future__ import annotations

import re
from typing import NamedTuple, Optional


class TemplateResult(NamedTuple):
    sql: str
    detail: str | None = None


_TEMPLATES: dict[str, TemplateResult] = {
    "total_count_icu_assets": TemplateResult(
        sql=(
            "SELECT COUNT(*) AS total_icu_assets FROM asset WHERE department ILIKE 'ICU' OR department = 'ICU'"
        ),
        detail="Total count of assets assigned to the ICU department.",
    ),
    "highest_downtime_device": TemplateResult(
        sql=(
            "SELECT a.asset_name, SUM(am.downtime_hours) AS total_downtime "
            "FROM asset_maintenance am JOIN asset a ON am.asset_id = a.asset_id "
            "GROUP BY a.asset_name ORDER BY total_downtime DESC LIMIT 1"
        ),
        detail="Device with highest total downtime.",
    ),
    "spare_parts_below_reorder": TemplateResult(
        sql=(
            "SELECT part_number, part_name, quantity_available, reorder_level "
            "FROM inventory WHERE quantity_available < reorder_level ORDER BY quantity_available ASC"
        ),
        detail="Spare parts below their reorder level.",
    ),
    "top_5_assets_by_downtime": TemplateResult(
        sql=(
            "SELECT a.asset_id, a.asset_name, SUM(am.downtime_hours) AS total_downtime "
            "FROM asset_maintenance am JOIN asset a ON am.asset_id = a.asset_id "
            "GROUP BY a.asset_id, a.asset_name ORDER BY total_downtime DESC LIMIT 5"
        ),
        detail="Top 5 assets by total downtime.",
    ),
    "count_assets_by_department": TemplateResult(
        sql=(
            "SELECT department, COUNT(*) AS asset_count FROM asset GROUP BY department ORDER BY asset_count DESC"
        ),
        detail="Count of assets grouped by department.",
    ),
    "average_downtime_per_asset_type": TemplateResult(
        sql=(
            "SELECT a.asset_type, AVG(am.downtime_hours) AS avg_downtime FROM asset_maintenance am "
            "JOIN asset a ON am.asset_id = a.asset_id "
            "GROUP BY a.asset_type ORDER BY avg_downtime DESC"
        ),
        detail="Average downtime per asset type.",
    ),
    "total_maintenance_cost_by_asset": TemplateResult(
        sql=(
            "SELECT a.asset_name, SUM(am.cost_of_parts) AS total_maintenance_cost FROM asset_maintenance am "
            "JOIN asset a ON am.asset_id = a.asset_id GROUP BY a.asset_name ORDER BY total_maintenance_cost DESC"
        ),
        detail="Total maintenance cost by asset.",
    ),
    "departments_with_most_assets": TemplateResult(
        sql=(
            "SELECT department, COUNT(*) AS asset_count FROM asset GROUP BY department ORDER BY asset_count DESC LIMIT 1"
        ),
        detail="Department with the highest number of assets.",
    ),
}


def route_question(question: str) -> Optional[TemplateResult]:
    """Simple deterministic router for common analytics questions.

    Matching strategy is intentionally conservative: keyword-based matching to avoid false-positives.
    """
    q = question.lower().strip()

    department_match = re.search(r"(?:how many|count)\s+assets\s+(?:are\s+)?(?:assigned\s+to|in)\s+([a-z0-9_\- ]+?)\s*\??$", q)
    if department_match:
        department = department_match.group(1).strip().upper()
        return TemplateResult(
            sql=(
                "SELECT COUNT(*) AS asset_count FROM asset "
                f"WHERE UPPER(department) = '{department}'"
            ),
            detail=f"Count of assets assigned to the {department} department.",
        )

    if ("count" in q or "total count" in q) and "icu" in q:
        return _TEMPLATES["total_count_icu_assets"]

    if ("highest downtime" in q) or ("highest" in q and "downtime" in q) or ("most downtime" in q):
        return _TEMPLATES["highest_downtime_device"]

    if ("spare part" in q or "spare parts" in q or "reorder" in q) and ("below" in q or "reorder level" in q):
        return _TEMPLATES["spare_parts_below_reorder"]

    if ("top 5" in q or "top five" in q) and "downtime" in q:
        return _TEMPLATES["top_5_assets_by_downtime"]

    if ("count assets by department" in q) or ("count assets" in q and "department" in q):
        return _TEMPLATES["count_assets_by_department"]

    if ("average downtime" in q or "avg downtime" in q) and "asset" in q:
        return _TEMPLATES["average_downtime_per_asset_type"]

    if "total maintenance cost" in q and "asset" in q:
        return _TEMPLATES["total_maintenance_cost_by_asset"]

    if ("highest number of assets" in q or "most assets" in q) and "department" in q:
        return _TEMPLATES["departments_with_most_assets"]

    return None
