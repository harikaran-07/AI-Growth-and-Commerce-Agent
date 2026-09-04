"""
Migration: add campaign policy columns (max_campaign_budget,
minimum_margin_percentage) to legacy policies tables.

SQLAlchemy create_all only creates missing TABLES - it never alters existing
tables, so legacy SQLite/Postgres databases need an explicit ALTER TABLE.
Duplicate-column errors are swallowed (non-fatal).
"""
import logging

from sqlalchemy import text

from models.database import async_session, IS_POSTGRES

logger = logging.getLogger(__name__)

_COLUMNS = [
    ("max_campaign_budget", "FLOAT DEFAULT 100000"),
    ("minimum_margin_percentage", "FLOAT DEFAULT 20"),
]


async def _table_exists(db) -> bool:
    stmt = (
        "SELECT tablename FROM pg_tables WHERE tablename='policies'"
        if IS_POSTGRES else
        "SELECT name FROM sqlite_master WHERE type='table' AND name='policies'"
    )
    result = await db.execute(text(stmt))
    return result.scalar() is not None


async def _column_exists(db, column: str) -> bool:
    if IS_POSTGRES:
        result = await db.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='policies' AND column_name=:col"
        ), {"col": column})
    else:
        result = await db.execute(text(
            "SELECT COUNT(*) FROM pragma_table_info('policies') WHERE name=:col"
        ), {"col": column})
    return bool(result.scalar())


async def migrate_policy_columns():
    """Ensure the policies table has the campaign-related columns."""
    async with async_session() as db:
        if not await _table_exists(db):
            logger.info("policies table not present yet - skipping column migration")
            return
        for column, ddl in _COLUMNS:
            try:
                if await _column_exists(db, column):
                    logger.info(f"policies.{column} already exists - skipping")
                    continue
                await db.execute(text(f"ALTER TABLE policies ADD COLUMN {column} {ddl}"))
                await db.commit()
                logger.info(f"Added policies.{column} ({ddl})")
            except Exception as e:
                # Duplicate column or concurrent migration - non-fatal.
                logger.warning(f"Could not add policies.{column}: {type(e).__name__}: {e}")
                await db.rollback()
