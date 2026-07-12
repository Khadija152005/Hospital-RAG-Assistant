"""
agents/scheduling_agent.py

Step 6 - The LangChain Agent that ties together the system prompt
(prompts/scheduling_prompt.py) and all 7 tools (tools/asset_tools.py,
tools/scheduling_tools.py) into one working "Hospital Scheduling
Optimization Assistant".

DESIGN NOTE ON TOOL GRANULARITY:
LLM tool-calling only passes text/JSON between tool calls -- it cannot
hold onto Python objects (like our Appointment dataclasses) between
turns. So, in addition to exposing individual tools (useful for
exploratory questions like "what's DIAL-008's status?"), we expose ONE
composite tool, `reroute_failed_asset`, that runs the full pipeline
(steps 1-2-3-4-5-7, and optionally 6) in a single call and returns the
final report. This keeps the underlying data flow 100% reliable (no risk
of the LLM mistyping an ID between steps) while the agent still reasons
about which tool to use and explains its steps to the user.

Run interactively with:
    py agents/scheduling_agent.py
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "tools"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "prompts"))

from asset_tools import (  # noqa: E402
    find_failed_asset,
    find_available_backup,
    AssetToolError,
)
from scheduling_tools import (  # noqa: E402
    get_today_schedule,
    generate_new_schedule,
    estimate_delay,
    update_schedule,
    generate_report,
    SchedulingToolError,
)
from scheduling_prompt import SCHEDULING_AGENT_SYSTEM_PROMPT  # noqa: E402

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Individual tools (exploratory / informational use by the agent)
# --------------------------------------------------------------------------

@tool
def check_asset_status(failure_status: str = "Corrective Maintenance") -> str:
    """
    Check which assets currently have a status matching `failure_status`
    (default: 'Corrective Maintenance', which means unplanned failure in
    this hospital's data). Use this to see if anything is currently down.
    """
    try:
        results = find_failed_asset(failure_status)
    except AssetToolError as exc:
        return f"Error checking asset status: {exc}"

    if not results:
        return f"No assets currently have status matching '{failure_status}'."

    lines = [
        f"{a.asset_id} | {a.asset_name} | type={a.asset_type} | dept={a.department} | status={a.status}"
        for a in results
    ]
    return "Assets found:\n" + "\n".join(lines)


@tool
def find_backup_candidates(failed_asset_id: str) -> str:
    """
    Find ranked backup asset candidates for the given failed asset_id.
    Candidates are ranked by same department first, then lowest workload.
    """
    try:
        backups = find_available_backup(failed_asset_id)
    except AssetToolError as exc:
        return f"Error: {exc}"

    if not backups:
        return f"No available backup found for {failed_asset_id}."

    lines = [
        f"{b.asset_id} | dept={b.department} | workload={b.workload} | status={b.status}"
        for b in backups
    ]
    return "Backup candidates (best first):\n" + "\n".join(lines)


@tool
def check_schedule(asset_id: str, date: str = "") -> str:
    """
    Get all appointments scheduled for `asset_id` on `date`
    (format: YYYY-MM-DD). Pass an empty string for `date` to default to
    today.
    """
    try:
        target = datetime.strptime(date, "%Y-%m-%d") if date else None
        appts = get_today_schedule(asset_id, target)
    except (ValueError, SchedulingToolError) as exc:
        return f"Error: {exc}"

    if not appts:
        return f"No appointments found for {asset_id} on that date."

    lines = [
        f"schedule_id={a.schedule_id} | {a.patient_name} | {a.scheduled_datetime} | "
        f"{a.procedure} | Dr. {a.doctor}"
        for a in appts
    ]
    return "Appointments:\n" + "\n".join(lines)


# --------------------------------------------------------------------------
# THE composite tool: runs the entire reassignment pipeline in one shot
# --------------------------------------------------------------------------

@tool
def reroute_failed_asset(
    asset_id: str,
    date: str = "",
    apply_changes: bool = False,
) -> str:
    """
    Run the FULL asset re-routing pipeline for a failed asset: confirms
    the failure, finds a backup, retrieves its appointments, generates
    an optimized reassignment, estimates delay, and returns a final
    report.

    Args:
        asset_id: The asset_id of the failed/down device (e.g. 'DIAL-008').
        date: Date (YYYY-MM-DD) to check appointments for. Pass an empty
            string to default to today.
        apply_changes: If True, actually WRITES the new schedule to the
            database. If False (default), only proposes the change --
            nothing is saved. Only set this True if the user explicitly
            asks to apply/save/confirm the reassignment.

    Returns:
        A formatted report string, ready to show the user.
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()

        # Step 1: confirm the asset is actually failed
        failed_assets = find_failed_asset(asset_id=asset_id)
        if not failed_assets:
            return (
                f"Asset '{asset_id}' does not currently have a failure status "
                f"(Corrective Maintenance). No action taken."
            )
        failed_status = failed_assets[0].status

        # Step 2: find backup
        backups = find_available_backup(asset_id)
        if not backups:
            original_schedule = get_today_schedule(asset_id, target_date)
            return generate_report(
                failed_asset_id=asset_id,
                failed_asset_status=failed_status,
                replacement_asset_id=None,
                original_schedule=original_schedule,
                new_schedule=[],
                estimated_delay_minutes=0,
                conflicts=["No backup asset available"],
                applied_to_database=False,
            )
        backup_asset_id = backups[0].asset_id

        # Step 3: get original schedule
        original_schedule = get_today_schedule(asset_id, target_date)

        # Step 4: generate new schedule
        new_schedule = generate_new_schedule(original_schedule, backup_asset_id)

        # Step 5: estimate delay
        delay = estimate_delay(original_schedule, new_schedule)

        # Step 6 (optional): apply to database
        applied = False
        if apply_changes and new_schedule:
            update_schedule(new_schedule)
            applied = True

        # Step 7: report
        report = generate_report(
            failed_asset_id=asset_id,
            failed_asset_status=failed_status,
            replacement_asset_id=backup_asset_id,
            original_schedule=original_schedule,
            new_schedule=new_schedule,
            estimated_delay_minutes=delay,
            conflicts=[],
            applied_to_database=applied,
        )
        return report

    except (AssetToolError, SchedulingToolError) as exc:
        return f"Error while rerouting {asset_id}: {exc}"
    except Exception as exc:  # noqa: BLE001 - agent-facing safety net
        logger.exception("Unexpected error in reroute_failed_asset")
        return f"Unexpected error while rerouting {asset_id}: {exc}"


# --------------------------------------------------------------------------
# Build the agent
# --------------------------------------------------------------------------

def build_agent():
    """Construct and return the compiled LangChain agent."""
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your .env file before "
            "running the agent. Get a free key at https://console.groq.com"
        )

    tools = [
        check_asset_status,
        find_backup_candidates,
        check_schedule,
        reroute_failed_asset,
    ]

    agent = create_agent(
        model="groq:llama-3.3-70b-versatile",
        tools=tools,
        system_prompt=SCHEDULING_AGENT_SYSTEM_PROMPT,
    )
    return agent


def run_query(agent, user_message: str) -> str:
    """Send one user message to the agent and return its final text reply."""
    result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})
    final_message = result["messages"][-1]
    return final_message.content


if __name__ == "__main__":
    print("Building Hospital Scheduling Optimization Assistant...")
    agent = build_agent()
    print("Ready. Type your request (or 'exit' to quit).\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        reply = run_query(agent, user_input)
        print(f"\nAssistant:\n{reply}\n")