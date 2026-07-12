"""
tools/scheduling_tools.py

Step 4 — Tools 3 through 7 of the Smart Asset Re-routing & Scheduling
Optimizer.

Works against the real discovered schema:

    procedure_schedule(schedule_id, patient_id, asset_id,
                        scheduled_datetime, status)
    person(person_id, first_name, last_name, gender, year_of_birth, race)
    staff(staff_id, full_name, role, department, email)
    asset_assignment(assignment_id, asset_id, staff_id)
    asset(asset_id, asset_name, asset_type, department, ...)

DATA GAPS (agreed with project owner in Step 3):
    - No "procedure name" column exists on procedure_schedule -> we use
      the asset's `asset_type` as a stand-in for "Procedure".
    - No "priority" column exists -> appointments are treated in strict
      chronological order (earliest scheduled_datetime = first
      reassigned), i.e. first-come-first-served.
    - "Doctor" is resolved via asset_assignment -> staff for the
      ORIGINAL (failed) asset. If multiple staff are assigned, all are
      listed; if none, "Unassigned" is shown.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "database"))
from db import db  # noqa: E402

logger = logging.getLogger(__name__)

# Average time (minutes) a machine needs per procedure, used to detect
# overlaps / estimate delay when the schedule doesn't define durations.
DEFAULT_PROCEDURE_DURATION_MINUTES = 30


class SchedulingToolError(RuntimeError):
    """Raised when a scheduling-tool operation fails."""


@dataclass
class Appointment:
    """A single patient appointment tied to an asset."""

    schedule_id: int
    patient_id: int
    patient_name: str
    asset_id: str
    scheduled_datetime: datetime
    status: str
    procedure: str  # stand-in: asset_type (see module docstring)
    doctor: str


# --------------------------------------------------------------------------
# Tool 3: get_today_schedule()
# --------------------------------------------------------------------------
def get_today_schedule(
    asset_id: str,
    target_date: Optional[datetime] = None,
) -> List[Appointment]:
    """
    Tool 3: get_today_schedule()

    Retrieve every appointment assigned to `asset_id` on `target_date`
    (defaults to today), ordered chronologically.

    Args:
        asset_id: The (failed) asset's ID.
        target_date: The date to filter on. Only the date portion is
            used. Defaults to today.

    Returns:
        List of Appointment, sorted by scheduled_datetime ascending.

    Raises:
        SchedulingToolError: on database failure.
    """
    day = (target_date or datetime.now()).date()
    day_start = datetime.combine(day, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    query = """
        SELECT
            ps.schedule_id,
            ps.patient_id,
            p.first_name,
            p.last_name,
            ps.asset_id,
            ps.scheduled_datetime,
            ps.status,
            a.asset_type,
            COALESCE(
                STRING_AGG(DISTINCT s.full_name, ', '),
                'Unassigned'
            ) AS doctor
        FROM procedure_schedule ps
        JOIN person p ON p.person_id = ps.patient_id
        JOIN asset a ON a.asset_id = ps.asset_id
        LEFT JOIN asset_assignment aa ON aa.asset_id = ps.asset_id
        LEFT JOIN staff s ON s.staff_id = aa.staff_id
        WHERE ps.asset_id = :asset_id
          AND ps.scheduled_datetime >= :day_start
          AND ps.scheduled_datetime < :day_end
          AND ps.status <> 'Cancelled'
        GROUP BY ps.schedule_id, ps.patient_id, p.first_name, p.last_name,
                 ps.asset_id, ps.scheduled_datetime, ps.status, a.asset_type
        ORDER BY ps.scheduled_datetime ASC
    """

    try:
        with db.session_scope() as session:
            rows = session.execute(
                text(query),
                {"asset_id": asset_id, "day_start": day_start, "day_end": day_end},
            ).mappings().all()
    except SQLAlchemyError as exc:
        logger.error("get_today_schedule failed: %s", exc)
        raise SchedulingToolError("Database error while fetching today's schedule.") from exc

    appointments = [
        Appointment(
            schedule_id=row["schedule_id"],
            patient_id=row["patient_id"],
            patient_name=f"{row['first_name'] or ''} {row['last_name'] or ''}".strip() or "Unknown",
            asset_id=row["asset_id"],
            scheduled_datetime=row["scheduled_datetime"],
            status=row["status"] or "Scheduled",
            procedure=row["asset_type"] or "Unknown Procedure",
            doctor=row["doctor"],
        )
        for row in rows
    ]

    if not appointments:
        logger.info("No appointments found for asset %s on %s.", asset_id, day)

    return appointments


# --------------------------------------------------------------------------
# Tool 4: generate_new_schedule()
# --------------------------------------------------------------------------
def generate_new_schedule(
    appointments: List[Appointment],
    backup_asset_id: str,
    procedure_duration_minutes: int = DEFAULT_PROCEDURE_DURATION_MINUTES,
) -> List[Appointment]:
    """
    Tool 4: generate_new_schedule()

    Reassign `appointments` (from the failed asset) onto `backup_asset_id`,
    preserving chronological order and avoiding overlaps with the backup
    machine's EXISTING appointments.

    Strategy:
        1. Fetch the backup asset's existing appointments for the same day.
        2. Walk through the failed asset's appointments in chronological
           order (already sorted by get_today_schedule).
        3. For each one, find the next free slot on the backup machine
           (>= the appointment's original time, not overlapping any
           existing or already-reassigned slot), assuming each procedure
           takes `procedure_duration_minutes`.

    Args:
        appointments: Appointments to reassign (typically the output of
            get_today_schedule() for the failed asset).
        backup_asset_id: The asset_id to reassign onto.
        procedure_duration_minutes: Assumed slot length per procedure.

    Returns:
        A new list of Appointment objects (copies) with updated
        `asset_id` and `scheduled_datetime` reflecting the optimized
        schedule. Original list is not mutated.

    Raises:
        SchedulingToolError: on database failure.
    """
    if not appointments:
        return []

    day = appointments[0].scheduled_datetime.date()

    try:
        existing_backup_slots = get_today_schedule(backup_asset_id, appointments[0].scheduled_datetime)
    except SchedulingToolError:
        raise

    # Build a list of occupied [start, end) intervals on the backup machine.
    occupied: List[tuple] = [
        (
            appt.scheduled_datetime,
            appt.scheduled_datetime + timedelta(minutes=procedure_duration_minutes),
        )
        for appt in existing_backup_slots
    ]

    def slot_is_free(start: datetime, end: datetime) -> bool:
        return all(end <= o_start or start >= o_end for o_start, o_end in occupied)

    new_schedule: List[Appointment] = []

    for appt in appointments:
        candidate_start = appt.scheduled_datetime
        # Push forward in duration-sized increments until we find a free slot.
        while True:
            candidate_end = candidate_start + timedelta(minutes=procedure_duration_minutes)
            if slot_is_free(candidate_start, candidate_end):
                break
            candidate_start += timedelta(minutes=procedure_duration_minutes)

        occupied.append((candidate_start, candidate_start + timedelta(minutes=procedure_duration_minutes)))

        new_schedule.append(
            Appointment(
                schedule_id=appt.schedule_id,
                patient_id=appt.patient_id,
                patient_name=appt.patient_name,
                asset_id=backup_asset_id,
                scheduled_datetime=candidate_start,
                status=appt.status,
                procedure=appt.procedure,
                doctor=appt.doctor,
            )
        )

    return new_schedule


# --------------------------------------------------------------------------
# Tool 5: estimate_delay()
# --------------------------------------------------------------------------
def estimate_delay(
    original_schedule: List[Appointment],
    new_schedule: List[Appointment],
) -> int:
    """
    Tool 5: estimate_delay()

    Estimate the average additional waiting time (in minutes) caused by
    reassignment, comparing each appointment's original time vs its new
    time.

    Args:
        original_schedule: Appointments before reassignment.
        new_schedule: Appointments after reassignment (same order/length
            as original_schedule, as produced by generate_new_schedule).

    Returns:
        Average delay in whole minutes (0 if no delay or no appointments).

    Raises:
        SchedulingToolError: if the two lists don't line up.
    """
    if len(original_schedule) != len(new_schedule):
        raise SchedulingToolError(
            "original_schedule and new_schedule must be the same length "
            "to estimate delay."
        )
    if not original_schedule:
        return 0

    total_delay_minutes = 0
    for original, new in zip(original_schedule, new_schedule):
        delta = (new.scheduled_datetime - original.scheduled_datetime).total_seconds() / 60
        total_delay_minutes += max(0, delta)  # ignore any "earlier" cases

    return round(total_delay_minutes / len(original_schedule))


# --------------------------------------------------------------------------
# Tool 6: update_schedule()  [optional / transactional]
# --------------------------------------------------------------------------
def update_schedule(new_schedule: List[Appointment]) -> int:
    """
    Tool 6: update_schedule()  (OPTIONAL — writes to the database)

    Apply the reassignment in `new_schedule` to the `procedure_schedule`
    table: updates asset_id and scheduled_datetime for each schedule_id.
    Wrapped in a single transaction — if any row fails, ALL changes are
    rolled back.

    Args:
        new_schedule: The output of generate_new_schedule().

    Returns:
        Number of rows successfully updated.

    Raises:
        SchedulingToolError: on any database error (transaction is
            rolled back before the error is raised).
    """
    if not new_schedule:
        return 0

    try:
        with db.session_scope() as session:  # commits on success, rolls back on error
            for appt in new_schedule:
                session.execute(
                    text(
                        """
                        UPDATE procedure_schedule
                        SET asset_id = :asset_id,
                            scheduled_datetime = :scheduled_datetime
                        WHERE schedule_id = :schedule_id
                        """
                    ),
                    {
                        "asset_id": appt.asset_id,
                        "scheduled_datetime": appt.scheduled_datetime,
                        "schedule_id": appt.schedule_id,
                    },
                )
        logger.info("Successfully updated %d appointment(s).", len(new_schedule))
        return len(new_schedule)

    except SQLAlchemyError as exc:
        logger.error("update_schedule failed, transaction rolled back: %s", exc)
        raise SchedulingToolError(
            "Failed to update the schedule in the database. No changes were saved."
        ) from exc


# --------------------------------------------------------------------------
# Tool 7: generate_report()
# --------------------------------------------------------------------------
def generate_report(
    failed_asset_id: str,
    failed_asset_status: str,
    replacement_asset_id: Optional[str],
    original_schedule: List[Appointment],
    new_schedule: List[Appointment],
    estimated_delay_minutes: int,
    conflicts: Optional[List[str]] = None,
    applied_to_database: bool = False,
) -> str:
    """
    Tool 7: generate_report()

    Build a clear, human-readable report for hospital staff, matching the
    format specified in the project brief.

    Returns:
        A formatted multi-line string report.
    """
    conflicts = conflicts or []
    affected_patients = len(original_schedule)
    reassigned_count = len(new_schedule)

    if replacement_asset_id is None:
        final_status = "FAILED — No backup machine available"
    elif conflicts:
        final_status = "Completed with Conflicts — Manual Review Needed"
    else:
        final_status = "Completed Successfully"

    lines = [
        "-" * 50,
        "Asset Failure Detected",
        "",
        f"Asset:",
        f"  {failed_asset_id}",
        "",
        f"Status:",
        f"  {failed_asset_status}",
        "",
        f"Replacement Machine:",
        f"  {replacement_asset_id or 'None found'}",
        "",
        f"Affected Patients:",
        f"  {affected_patients}",
        "",
        f"Appointments Reassigned:",
        f"  {reassigned_count}",
        "",
        f"Estimated Delay:",
        f"  {estimated_delay_minutes} minutes",
        "",
        f"Conflicts:",
        f"  {', '.join(conflicts) if conflicts else 'None'}",
        "",
        f"Database Updated:",
        f"  {'Yes' if applied_to_database else 'No (report only)'}",
        "",
        f"Final Status:",
        f"  {final_status}",
        "-" * 50,
    ]

    if new_schedule:
        lines.append("\nDetailed Reassignments:")
        for original, new in zip(original_schedule, new_schedule):
            lines.append(
                f"  - {new.patient_name} | {original.scheduled_datetime.strftime('%H:%M')} "
                f"-> {new.scheduled_datetime.strftime('%H:%M')} | "
                f"{new.procedure} | Dr. {new.doctor}"
            )

    return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
    print("This module is meant to be imported by the agent. "
          "Run 'py agents/scheduling_agent.py' once Step 6 is built, "
          "or import individual functions to test manually.")