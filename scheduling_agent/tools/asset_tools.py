"""
tools/asset_tools.py

Step 4 — Tools 1 & 2 of the Smart Asset Re-routing & Scheduling Optimizer.

These tools work against the REAL discovered schema (see
database/schema_explorer.py output):

    asset(asset_id, asset_name, asset_type, department, manufacturer,
          model, serial_number, purchase_date, purchase_cost,
          expected_lifetime_years, operating_hours,
          calibration_interval_hours)

    asset_status_log(status_id, asset_id, status, start_time, end_time)
        - The CURRENT status of an asset is the row for that asset_id
          with the latest start_time where end_time IS NULL (still open).
          If every row has an end_time, we fall back to the row with the
          most recent start_time.

    procedure_schedule(schedule_id, patient_id, asset_id,
                        scheduled_datetime, status)
        - Used here only to measure workload when ranking backup assets.

NOTE ON DATA GAPS (confirmed with project owner):
    - There is no explicit "location" column on `asset`; we use
      `department` as the location/grouping signal, as agreed.
    - Status strings ("Major Failure", "Available", etc.) are whatever
      values exist in `asset_status_log.status` — we do NOT hardcode a
      closed list, we just filter case-insensitively on what's passed in,
      so this keeps working even if the team's naming changes slightly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "database"))
from db import db  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_FAILURE_STATUS = "Corrective Maintenance"
DEFAULT_AVAILABLE_STATUS = "Operational"


@dataclass
class AssetInfo:
    """Represents a single asset with its current status."""

    asset_id: str
    asset_name: Optional[str]
    asset_type: Optional[str]
    department: Optional[str]  # doubles as "location" (see note above)
    status: Optional[str]
    workload: int = field(default=0)  # # of upcoming scheduled procedures


class AssetToolError(RuntimeError):
    """Raised when an asset-tool operation fails (DB error, bad input, etc.)."""


def _get_current_status_subquery() -> str:
    """
    Returns a SQL snippet (as a CTE) that resolves each asset's CURRENT
    status: prefer the still-open row (end_time IS NULL); otherwise use
    the most recent start_time.
    """
    return """
    WITH current_status AS (
        SELECT DISTINCT ON (asset_id)
            asset_id,
            status,
            start_time,
            end_time
        FROM asset_status_log
        ORDER BY asset_id,
                 (end_time IS NULL) DESC,   -- open rows first
                 start_time DESC
    )
    """


def find_failed_asset(
    failure_status: str = DEFAULT_FAILURE_STATUS,
    asset_id: Optional[str] = None,
) -> List[AssetInfo]:
    """
    Tool 1: find_failed_asset()

    Search for asset(s) whose CURRENT status matches `failure_status`
    (default: "Major Failure").

    Args:
        failure_status: The status string to match (case-insensitive,
            partial match e.g. "failure" matches "Major Failure").
        asset_id: Optional — if provided, restrict the search to this
            specific asset (useful when the user already names the
            failed device, e.g. "CT Scanner A").

    Returns:
        A list of AssetInfo for every asset currently in a failed state
        (usually 0 or 1 result, but returns all matches).

    Raises:
        AssetToolError: on database failure.
    """
    query = _get_current_status_subquery() + """
        SELECT
            a.asset_id,
            a.asset_name,
            a.asset_type,
            a.department,
            cs.status
        FROM asset a
        JOIN current_status cs ON cs.asset_id = a.asset_id
        WHERE cs.status ILIKE :status_pattern
    """
    params = {"status_pattern": f"%{failure_status}%"}

    if asset_id:
        query += " AND a.asset_id = :asset_id"
        params["asset_id"] = asset_id

    try:
        with db.session_scope() as session:
            rows = session.execute(text(query), params).mappings().all()
    except SQLAlchemyError as exc:
        logger.error("find_failed_asset failed: %s", exc)
        raise AssetToolError("Database error while searching for failed assets.") from exc

    results = [
        AssetInfo(
            asset_id=row["asset_id"],
            asset_name=row["asset_name"],
            asset_type=row["asset_type"],
            department=row["department"],
            status=row["status"],
        )
        for row in rows
    ]

    if not results:
        logger.info("No assets found with status matching '%s'.", failure_status)

    return results


def find_available_backup(
    failed_asset_id: str,
    available_status: str = DEFAULT_AVAILABLE_STATUS,
) -> List[AssetInfo]:
    """
    Tool 2: find_available_backup()

    Find candidate replacement assets for `failed_asset_id`:
        - Same asset_type as the failed asset
        - Status currently matches `available_status`
        - NOT the failed asset itself

    Candidates are ranked (best first) by:
        1. Same department as the failed asset (preferred / tie-breaker)
        2. Lowest workload (fewest upcoming scheduled procedures)

    Args:
        failed_asset_id: The asset_id of the failed device.
        available_status: Status string meaning "ready to use"
            (default: "Available").

    Returns:
        A ranked list of AssetInfo candidates, best candidate first.
        Empty list if no backup exists.

    Raises:
        AssetToolError: on database failure, or if failed_asset_id
            doesn't exist.
    """
    try:
        with db.session_scope() as session:
            # 1. Look up the failed asset's type & department first.
            failed_row = session.execute(
                text("SELECT asset_type, department FROM asset WHERE asset_id = :aid"),
                {"aid": failed_asset_id},
            ).mappings().first()

            if failed_row is None:
                raise AssetToolError(
                    f"Asset '{failed_asset_id}' does not exist in the database."
                )

            asset_type = failed_row["asset_type"]
            department = failed_row["department"]

            # 2. Find same-type, currently-available candidates.
            query = _get_current_status_subquery() + """
                SELECT
                    a.asset_id,
                    a.asset_name,
                    a.asset_type,
                    a.department,
                    cs.status,
                    COALESCE(ps.workload, 0) AS workload
                FROM asset a
                JOIN current_status cs ON cs.asset_id = a.asset_id
                LEFT JOIN (
                    SELECT asset_id, COUNT(*) AS workload
                    FROM procedure_schedule
                    WHERE scheduled_datetime >= NOW()
                      AND status <> 'Cancelled'
                    GROUP BY asset_id
                ) ps ON ps.asset_id = a.asset_id
                WHERE a.asset_type = :asset_type
                  AND a.asset_id <> :failed_asset_id
                  AND cs.status ILIKE :available_pattern
            """
            rows = session.execute(
                text(query),
                {
                    "asset_type": asset_type,
                    "failed_asset_id": failed_asset_id,
                    "available_pattern": f"%{available_status}%",
                },
            ).mappings().all()

    except AssetToolError:
        raise
    except SQLAlchemyError as exc:
        logger.error("find_available_backup failed: %s", exc)
        raise AssetToolError("Database error while searching for backup assets.") from exc

    candidates = [
        AssetInfo(
            asset_id=row["asset_id"],
            asset_name=row["asset_name"],
            asset_type=row["asset_type"],
            department=row["department"],
            status=row["status"],
            workload=row["workload"],
        )
        for row in rows
    ]

    # Rank: same department first (0 = match, 1 = no match), then lowest workload.
    candidates.sort(key=lambda c: (c.department != department, c.workload))

    if not candidates:
        logger.info(
            "No available backup found for asset_type='%s' (failed asset %s).",
            asset_type,
            failed_asset_id,
        )

    return candidates


if __name__ == "__main__":
    # Manual smoke test: `py tools/asset_tools.py`
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")

    failed = find_failed_asset()
    print(f"\nFailed assets found: {len(failed)}")
    for a in failed:
        print(f"  - {a.asset_id} | {a.asset_name} | {a.asset_type} | {a.department} | {a.status}")

    if failed:
        backups = find_available_backup(failed[0].asset_id)
        print(f"\nBackup candidates for {failed[0].asset_id}: {len(backups)}")
        for b in backups:
            print(f"  - {b.asset_id} | {b.department} | workload={b.workload} | {b.status}")