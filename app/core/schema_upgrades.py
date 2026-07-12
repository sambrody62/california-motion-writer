"""
Additive, idempotent column upgrades applied after create_all.

This repo has no alembic: create_all only creates missing TABLES, so a new
column on an existing table must be added here. Nullable additions only.
"""
import logging
from typing import List, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger(__name__)

# (table, column, SQL type) — append-only
COLUMN_UPGRADES: List[Tuple[str, str, str]] = [
    ("motions", "fact_check", "JSON"),
]


async def _sqlite_has_column(conn: AsyncConnection, table: str, column: str) -> bool:
    rows = await conn.execute(text(f"PRAGMA table_info({table})"))
    return column in {row[1] for row in rows}


async def apply_column_upgrades(conn: AsyncConnection) -> None:
    """Add any missing COLUMN_UPGRADES columns. Idempotent on SQLite and Postgres."""
    dialect = conn.dialect.name
    for table, column, sql_type in COLUMN_UPGRADES:
        if dialect == "sqlite":
            if await _sqlite_has_column(conn, table, column):
                continue
            await conn.execute(
                text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}")
            )
        else:
            await conn.execute(
                text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {sql_type}")
            )
        logger.info("Schema upgrade applied: %s.%s (%s)", table, column, sql_type)
