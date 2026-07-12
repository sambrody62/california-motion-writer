"""
motions.fact_check must exist even on databases created before the column
existed. This repo has no alembic — Database.create_tables applies additive,
idempotent column upgrades (app/core/schema_upgrades.py) after create_all.
"""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database import Database

# Registers all models (incl. Motion) on Base.metadata
import app.models.motion  # noqa: F401

pytestmark = pytest.mark.asyncio


async def _motions_columns(engine) -> set:
    async with engine.connect() as conn:
        rows = await conn.execute(text("PRAGMA table_info(motions)"))
        return {row[1] for row in rows}


async def _database_with_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    database = Database()
    database.engine = engine
    return database, engine


async def test_fresh_create_tables_has_fact_check_column():
    database, engine = await _database_with_engine()
    await database.create_tables()
    assert "fact_check" in await _motions_columns(engine)
    await engine.dispose()


async def test_create_tables_adds_fact_check_to_legacy_motions_table():
    """A motions table created before the column existed gets it added."""
    database, engine = await _database_with_engine()
    async with engine.begin() as conn:
        await conn.execute(
            text("CREATE TABLE motions (id VARCHAR(36) NOT NULL PRIMARY KEY)")
        )
    await database.create_tables()

    columns = await _motions_columns(engine)
    assert "fact_check" in columns
    await engine.dispose()


async def test_create_tables_upgrade_is_idempotent():
    database, engine = await _database_with_engine()
    await database.create_tables()
    await database.create_tables()  # second run must not raise
    assert "fact_check" in await _motions_columns(engine)
    await engine.dispose()
