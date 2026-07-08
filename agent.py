"""
Automated Inventory & Supply Chain Agent
=========================================
Uses LangChain AgentExecutor + Claude to autonomously:
  1. Fetch the upcoming week's procedure schedule
  2. Cross-reference with current inventory levels
  3. Detect shortages before they happen
  4. Create restock alerts
  5. Draft purchase orders for critical items

Run:
    python agent.py                    # one-shot weekly check
    python agent.py --query "..."      # ask the agent a custom question
"""

import argparse
import os
import sys

from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage

from tools import (
    get_upcoming_procedures,
    get_inventory_levels,
    get_items_below_reorder,
    check_supply_sufficiency,
    create_restock_alert,
    draft_purchase_order,
    get_all_purchase_orders,
)

# ── Model ──────────────────────────────────────────────────────────────────────

llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    temperature=0,
    max_tokens=4096,
)

# ── Tools list ─────────────────────────────────────────────────────────────────

tools = [
    get_upcoming_procedures,
    get_inventory_levels,
    get_items_below_reorder,
    check_supply_sufficiency,
    create_restock_alert,
    draft_purchase_order,
    get_all_purchase_orders,
]

# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the Automated Inventory & Supply Chain Agent for a hospital asset management system.

Your mission:
- Prevent shortages of critical medical supplies and spare parts BEFORE they happen.
- Cross-reference upcoming procedure schedules with current inventory levels.
- Detect items that will run out or fall below reorder levels during the upcoming period.
- Create restock alerts and draft purchase orders autonomously for critical shortages.

Workflow for a routine weekly check:
1. Call get_upcoming_procedures(days_ahead=7) to see what's scheduled.
2. Call get_items_below_reorder() for an immediate snapshot of low stock.
3. For each supply item that appears in the upcoming procedures, call check_supply_sufficiency(item_name, days_ahead=7).
4. For every item where shortage_alert=true:
   a. Call create_restock_alert(...) to log it.
   b. Call draft_purchase_order(...) with urgency='URGENT' if procedure_count > 0, else 'HIGH'.
5. Summarize all findings clearly: list critical shortages, items at risk, and the PO numbers created.

Rules:
- Be proactive, not reactive. If stock will fall below reorder level after upcoming procedures, that IS a shortage.
- Always include the PO number in your summary so staff can track it.
- If the user asks a custom question, answer it using the available tools.
- Keep your final summary structured: Critical Shortages → At-Risk Items → Purchase Orders Created → All Clear Items.
"""

# ── Prompt template ────────────────────────────────────────────────────────────

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# ── Agent ──────────────────────────────────────────────────────────────────────

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,          # set False in production
    max_iterations=20,     # enough for a full weekly scan
    return_intermediate_steps=True,
)

# ── Runner ─────────────────────────────────────────────────────────────────────

WEEKLY_CHECK_PROMPT = (
    "Run the full weekly inventory check. "
    "Fetch the procedure schedule for the next 7 days, check all required supplies, "
    "identify any shortages, create restock alerts, and draft purchase orders for "
    "all critical and at-risk items. Provide a structured summary at the end."
)


def run_agent(query: str) -> None:
    print("\n" + "=" * 60)
    print("SUPPLY CHAIN AGENT")
    print("=" * 60)
    print(f"Task: {query}\n")

    result = agent_executor.invoke({"input": query})

    print("\n" + "=" * 60)
    print("AGENT FINAL RESPONSE")
    print("=" * 60)
    print(result["output"])


def main():
    parser = argparse.ArgumentParser(description="Hospital Inventory & Supply Chain Agent")
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Custom question for the agent. Omit for a full weekly check.",
    )
    args = parser.parse_args()

    query = args.query if args.query else WEEKLY_CHECK_PROMPT
    run_agent(query)


if __name__ == "__main__":
    main()
