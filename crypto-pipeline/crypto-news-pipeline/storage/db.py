"""
SQLite storage via SQLAlchemy Core. The table matches the unified schema
exactly. Inserts are idempotent — duplicates (same id) are skipped.
"""

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Column,
    Float,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    select,
)
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DB_PATH, SCHEMA_FIELDS  # noqa: E402

logger = logging.getLogger(__name__)

metadata = MetaData()

records_table = Table(
    "records",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("source_type", String(32), nullable=False),
    Column("source_name", String(64), nullable=False),
    Column("title", Text, nullable=False),
    Column("url", Text, nullable=False),
    Column("published_at", String(40), nullable=False),
    Column("content", Text, nullable=False),
    Column("collected_at", String(40), nullable=False),
    Column("event_category", String(48), nullable=False),
    Column("affected_coins", Text, nullable=False),
    Column("sentiment_score", Float, nullable=False),
    Column("importance_score", Float, nullable=False),
)


def get_engine(db_path: Optional[Path] = None) -> Engine:
    """Create an engine for the given SQLite file (default: config.DB_PATH),
    creating the parent directory and table if needed."""
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}")
    metadata.create_all(engine)
    return engine


def insert_record(engine: Engine, record: dict) -> bool:
    """Insert one record. Returns True if inserted, False if a duplicate id
    already existed (skipped)."""
    stmt = sqlite_insert(records_table).values(
        **{field: record[field] for field in SCHEMA_FIELDS}
    ).on_conflict_do_nothing(index_elements=["id"])
    with engine.begin() as conn:
        result = conn.execute(stmt)
    return bool(result.rowcount)


def save_batch(engine: Engine, records: list[dict]) -> int:
    """Insert a batch of records, skipping duplicates. Returns the number of
    NEW rows actually inserted."""
    if not records:
        return 0
    inserted = 0
    with engine.begin() as conn:
        for record in records:
            stmt = sqlite_insert(records_table).values(
                **{field: record[field] for field in SCHEMA_FIELDS}
            ).on_conflict_do_nothing(index_elements=["id"])
            result = conn.execute(stmt)
            inserted += result.rowcount
    logger.info("DB: %d/%d new records inserted (rest were duplicates)", inserted, len(records))
    return inserted


def get_all_records(engine: Engine) -> list[dict]:
    """Return every stored record as a dict, newest published first."""
    stmt = select(records_table).order_by(records_table.c.published_at.desc())
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    return [dict(row) for row in rows]


def get_records_since(engine: Engine, hours: int) -> list[dict]:
    """Return records published within the last N hours (by published_at)."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    stmt = (
        select(records_table)
        .where(records_table.c.published_at >= cutoff)
        .order_by(records_table.c.published_at.desc())
    )
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    return [dict(row) for row in rows]


def count_records(engine: Engine) -> int:
    """Total number of stored records."""
    with engine.connect() as conn:
        return conn.execute(select(records_table.c.id)).mappings().all().__len__()
