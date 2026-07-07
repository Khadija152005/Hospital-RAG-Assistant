"""
Inventory & Supply Chain Agent — Database Tools
Uses LangChain tool decorators to expose PostgreSQL queries to the agent.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional

import psycopg2
import psycopg2.extras
from langchain.tools import tool


# ── DB connection ──────────────────────────────────────────────────────────────

DB_CONFIG = {
    "host":     os.getenv("PGHOST",     "ep-morning-resonance-agormtr5-pooler.c-2.eu-central-1.aws.neon.tech"),
    "dbname":   os.getenv("PGDATABASE", "neondb"),
    "user":     os.getenv("PGUSER",     "neondb_owner"),
    "password": os.getenv("PGPASSWORD", "npg_NpblLYw9Qa1C"),
    "sslmode":  os.getenv("PGSSLMODE",  "require"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def run_query(sql: str, params=None) -> list[dict]:
    """Execute a SELECT query and return rows as a list of dicts."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


def run_write(sql: str, params=None) -> int:
    """Execute an INSERT/UPDATE and return affected row count."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount


# ── Tools ──────────────────────────────────────────────────────────────────────

@tool
def get_upcoming_procedures(days_ahead: int = 7) -> str:
    """
    Fetch all scheduled procedures for the next N days (default 7).
    Returns procedure type, required supplies, scheduled date, and quantity.
    Use this first to understand what supplies will be needed.
    """
    cutoff = datetime.now() + timedelta(days=days_ahead)
    rows = run_query(
        """
        SELECT
            ps.procedure_id,
            ps.procedure_type,
            ps.scheduled_date,
            ps.required_supply_item,
            ps.required_supply_quantity,
            ps.asset_id,
            ps.patient_id
        FROM procedure_schedule ps
        WHERE ps.scheduled_date BETWEEN NOW() AND %s
        ORDER BY ps.scheduled_date ASC
        """,
        (cutoff,),
    )
    if not rows:
        return "No procedures scheduled in the next {} days.".format(days_ahead)
    return json.dumps(rows, default=str)


@tool
def get_inventory_levels(item_name: Optional[str] = None) -> str:
    """
    Get current inventory levels for all items, or filter by item name.
    Returns item name, current quantity, reorder level, unit, and supplier info.
    Use this to check if stock is sufficient for upcoming procedures.
    """
    if item_name:
        rows = run_query(
            """
            SELECT
                item_id,
                item_name,
                current_quantity,
                reorder_level,
                unit,
                supplier_name,
                supplier_contact,
                lead_time_days
            FROM inventory
            WHERE item_name ILIKE %s
            ORDER BY item_name
            """,
            (f"%{item_name}%",),
        )
    else:
        rows = run_query(
            """
            SELECT
                item_id,
                item_name,
                current_quantity,
                reorder_level,
                unit,
                supplier_name,
                supplier_contact,
                lead_time_days
            FROM inventory
            ORDER BY item_name
            """
        )
    if not rows:
        return "No inventory items found."
    return json.dumps(rows, default=str)


@tool
def get_items_below_reorder() -> str:
    """
    Returns all inventory items where current_quantity is at or below the reorder_level.
    Use this for a quick scan of everything that needs restocking regardless of procedures.
    """
    rows = run_query(
        """
        SELECT
            item_id,
            item_name,
            current_quantity,
            reorder_level,
            unit,
            supplier_name,
            supplier_contact,
            lead_time_days,
            (reorder_level - current_quantity) AS shortage_gap
        FROM inventory
        WHERE current_quantity <= reorder_level
        ORDER BY shortage_gap DESC
        """
    )
    if not rows:
        return "All inventory items are above their reorder levels."
    return json.dumps(rows, default=str)


@tool
def check_supply_sufficiency(supply_item: str, days_ahead: int = 7) -> str:
    """
    Cross-references a specific supply item against upcoming procedure demand.
    Returns current stock, total demand for the period, and whether a shortage will occur.
    
    Args:
        supply_item: The name of the supply item to check (e.g., 'MRI Helium', 'Dialyzers').
        days_ahead: How many days ahead to look for procedures (default 7).
    """
    cutoff = datetime.now() + timedelta(days=days_ahead)

    # Current stock
    stock_rows = run_query(
        """
        SELECT item_name, current_quantity, reorder_level, unit, lead_time_days
        FROM inventory
        WHERE item_name ILIKE %s
        LIMIT 1
        """,
        (f"%{supply_item}%",),
    )

    # Demand from procedures
    demand_rows = run_query(
        """
        SELECT
            required_supply_item,
            SUM(required_supply_quantity) AS total_demand,
            COUNT(*) AS procedure_count
        FROM procedure_schedule
        WHERE required_supply_item ILIKE %s
          AND scheduled_date BETWEEN NOW() AND %s
        GROUP BY required_supply_item
        """,
        (f"%{supply_item}%", cutoff),
    )

    if not stock_rows:
        return f"Item '{supply_item}' not found in inventory."

    stock = stock_rows[0]
    current_qty = stock["current_quantity"]
    reorder_lvl = stock["reorder_level"]

    total_demand = 0
    procedure_count = 0
    if demand_rows:
        total_demand = demand_rows[0]["total_demand"] or 0
        procedure_count = demand_rows[0]["procedure_count"] or 0

    remaining_after = current_qty - total_demand
    will_shortage = remaining_after < reorder_lvl

    result = {
        "item": stock["item_name"],
        "unit": stock["unit"],
        "current_stock": current_qty,
        "reorder_level": reorder_lvl,
        "demand_next_{}_days".format(days_ahead): total_demand,
        "procedure_count": procedure_count,
        "stock_after_procedures": remaining_after,
        "shortage_alert": will_shortage,
        "lead_time_days": stock["lead_time_days"],
        "recommendation": (
            "URGENT: Order immediately — stock will drop below reorder level."
            if will_shortage
            else "Stock is sufficient for the upcoming period."
        ),
    }
    return json.dumps(result, default=str)


@tool
def create_restock_alert(item_name: str, current_qty: float, required_qty: float, reason: str) -> str:
    """
    Logs a restock alert to the database for tracking and audit purposes.
    
    Args:
        item_name: The name of the inventory item.
        current_qty: Current quantity in stock.
        required_qty: Quantity needed for upcoming procedures.
        reason: Brief explanation of why the alert was triggered.
    """
    rows = run_query(
        "SELECT item_id FROM inventory WHERE item_name ILIKE %s LIMIT 1",
        (f"%{item_name}%",),
    )
    if not rows:
        return f"Could not find item '{item_name}' in inventory to log alert."

    item_id = rows[0]["item_id"]
    run_write(
        """
        INSERT INTO restock_alerts
            (item_id, item_name, current_quantity, required_quantity, reason, created_at, status)
        VALUES
            (%s, %s, %s, %s, %s, NOW(), 'OPEN')
        """,
        (item_id, item_name, current_qty, required_qty, reason),
    )
    return f"Restock alert created for '{item_name}': current={current_qty}, needed={required_qty}."


@tool
def draft_purchase_order(
    item_name: str,
    quantity_to_order: float,
    urgency: str = "NORMAL",
    notes: str = "",
) -> str:
    """
    Drafts a purchase order for a supply item and saves it to the database.
    
    Args:
        item_name: The item to order.
        quantity_to_order: How much to order.
        urgency: 'URGENT', 'HIGH', or 'NORMAL'.
        notes: Any additional context for the procurement team.
    """
    inv_rows = run_query(
        """
        SELECT item_id, item_name, unit, supplier_name, supplier_contact, lead_time_days
        FROM inventory
        WHERE item_name ILIKE %s
        LIMIT 1
        """,
        (f"%{item_name}%",),
    )
    if not inv_rows:
        return f"Cannot create PO: item '{item_name}' not found in inventory."

    item = inv_rows[0]
    po_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{item['item_id']}"

    run_write(
        """
        INSERT INTO purchase_orders
            (po_number, item_id, item_name, quantity, unit, supplier_name,
             supplier_contact, urgency, notes, status, created_at, created_by)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'DRAFT', NOW(), 'SUPPLY_CHAIN_AGENT')
        """,
        (
            po_number,
            item["item_id"],
            item["item_name"],
            quantity_to_order,
            item["unit"],
            item["supplier_name"],
            item["supplier_contact"],
            urgency.upper(),
            notes,
        ),
    )

    return json.dumps(
        {
            "status": "DRAFT_CREATED",
            "po_number": po_number,
            "item": item["item_name"],
            "quantity": quantity_to_order,
            "unit": item["unit"],
            "supplier": item["supplier_name"],
            "supplier_contact": item["supplier_contact"],
            "urgency": urgency.upper(),
            "estimated_lead_time_days": item["lead_time_days"],
            "notes": notes,
        }
    )


@tool
def get_all_purchase_orders(status: Optional[str] = None) -> str:
    """
    Retrieves all purchase orders, optionally filtered by status.
    Status options: 'DRAFT', 'SENT', 'CONFIRMED', 'RECEIVED', 'CANCELLED'.
    """
    if status:
        rows = run_query(
            """
            SELECT * FROM purchase_orders
            WHERE status = %s
            ORDER BY created_at DESC
            """,
            (status.upper(),),
        )
    else:
        rows = run_query(
            "SELECT * FROM purchase_orders ORDER BY created_at DESC"
        )
    if not rows:
        return "No purchase orders found."
    return json.dumps(rows, default=str)
