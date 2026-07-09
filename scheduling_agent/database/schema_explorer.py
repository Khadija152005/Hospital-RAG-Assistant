"""
database/schema_explorer.py

Step 2: Automatic database schema discovery.

This script connects to the Neon PostgreSQL database (using the existing
`db` engine from `database/db.py`) and dynamically inspects it:

    - Lists every table in the 'public' schema
    - Lists every column per table (name, type, nullability, default)
    - Lists primary keys per table
    - Lists foreign keys per table (which table/column they reference)
    - Prints a clean, readable schema report to the console

No table or column names are assumed or hardcoded — everything is
discovered dynamically via SQLAlchemy's `inspect()` API. This report is
what we'll use in Step 3 to identify which tables are relevant to the
Smart Asset Re-routing & Scheduling Optimizer module.

Run directly with:
    py database/schema_explorer.py
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sqlalchemy import inspect
from sqlalchemy.engine import Engine

# Import the already-configured engine/singleton from db.py
from db import db  # when run as `py database/schema_explorer.py` from HospitalAgent/

logger = logging.getLogger(__name__)


def get_schema_report(engine: Engine, schema: str = "public") -> Dict[str, Any]:
    """
    Inspect the database and build a structured report describing every
    table, its columns, primary keys, and foreign keys.

    Args:
        engine: A live SQLAlchemy Engine.
        schema: The Postgres schema to inspect (default 'public').

    Returns:
        A dict of the form:
        {
            "table_name": {
                "columns": [ {name, type, nullable, default}, ... ],
                "primary_keys": [ "col1", ... ],
                "foreign_keys": [
                    {"column": "...", "references_table": "...", "references_column": "..."},
                    ...
                ],
            },
            ...
        }
    """
    inspector = inspect(engine)
    report: Dict[str, Any] = {}

    table_names = inspector.get_table_names(schema=schema)

    for table_name in sorted(table_names):
        columns_info: List[Dict[str, Any]] = []
        for col in inspector.get_columns(table_name, schema=schema):
            columns_info.append(
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": col.get("default"),
                }
            )

        pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
        primary_keys = pk_constraint.get("constrained_columns", []) or []

        fks_info: List[Dict[str, str]] = []
        for fk in inspector.get_foreign_keys(table_name, schema=schema):
            local_cols = fk.get("constrained_columns", [])
            remote_table = fk.get("referred_table")
            remote_cols = fk.get("referred_columns", [])
            for local_col, remote_col in zip(local_cols, remote_cols):
                fks_info.append(
                    {
                        "column": local_col,
                        "references_table": remote_table,
                        "references_column": remote_col,
                    }
                )

        report[table_name] = {
            "columns": columns_info,
            "primary_keys": primary_keys,
            "foreign_keys": fks_info,
        }

    return report


def print_schema_report(report: Dict[str, Any]) -> None:
    """Pretty-print the schema report to the console in a readable format."""
    if not report:
        print("No tables found in the database.")
        return

    print("=" * 70)
    print(f"DATABASE SCHEMA REPORT  ({len(report)} table(s) found)")
    print("=" * 70)

    for table_name, info in report.items():
        print(f"\nTABLE: {table_name}")
        print("-" * 70)

        print("  Columns:")
        for col in info["columns"]:
            pk_marker = " [PK]" if col["name"] in info["primary_keys"] else ""
            null_marker = "NULL" if col["nullable"] else "NOT NULL"
            default = f", default={col['default']}" if col["default"] else ""
            print(
                f"    - {col['name']:<25} {col['type']:<20} {null_marker}{default}{pk_marker}"
            )

        if info["foreign_keys"]:
            print("  Foreign Keys:")
            for fk in info["foreign_keys"]:
                print(
                    f"    - {fk['column']} -> {fk['references_table']}.{fk['references_column']}"
                )
        else:
            print("  Foreign Keys: (none)")

    print("\n" + "=" * 70)
    print("END OF SCHEMA REPORT")
    print("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
    schema_report = get_schema_report(db.engine)
    print_schema_report(schema_report)