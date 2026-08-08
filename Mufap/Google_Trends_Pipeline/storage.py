"""
storage.py — Stage 5: Data Storage

SQLite storage layer. Keeps two tables:
  - google_trends_raw      : what was actually collected, minimally touched
  - google_trends_features : cleaned + normalized + engineered features —
                              this is the structured output the central
                              prediction engine integrates against

Both tables are keyed by (keyword, date), so repeated pipeline runs
upsert rather than duplicate rows.
"""

import json
import sqlite3
from datetime import datetime, timezone

DB_PATH = "alt_data.db"


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS google_trends_raw (
            keyword    TEXT NOT NULL,
            date       TEXT NOT NULL,
            interest   INTEGER,
            is_partial INTEGER,
            fetched_at TEXT,
            PRIMARY KEY (keyword, date)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS google_trends_features (
            keyword        TEXT NOT NULL,
            date           TEXT NOT NULL,
            interest       REAL,
            interest_norm  REAL,
            rolling_avg_7d REAL,
            pct_change_7d  REAL,
            zscore_30d     REAL,
            processed_at   TEXT,
            PRIMARY KEY (keyword, date)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS google_trends_common (
            id                  TEXT PRIMARY KEY,
            source              TEXT,
            source_type         TEXT,
            url                 TEXT,
            title               TEXT,
            description         TEXT,
            full_text           TEXT,
            published_time_utc  TEXT,
            ingestion_time_utc  TEXT,
            country             TEXT,
            region              TEXT,
            language            TEXT,
            asset_class         TEXT,
            market              TEXT,
            sector              TEXT,
            event_type          TEXT,
            importance_score    REAL,
            sentiment_score     REAL,
            confidence_score    REAL,
            keywords            TEXT,
            named_entities      TEXT,
            related_assets      TEXT,
            raw_response        TEXT
        )
        """
    )
    conn.commit()
    return conn


def upsert_raw(conn: sqlite3.Connection, records: list[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    for r in records:
        cur.execute(
            """
            INSERT INTO google_trends_raw (keyword, date, interest, is_partial, fetched_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(keyword, date) DO UPDATE SET
                interest=excluded.interest,
                is_partial=excluded.is_partial,
                fetched_at=excluded.fetched_at
            """,
            (r["keyword"], r["date"], r["interest"], int(r["is_partial"]), now),
        )
    conn.commit()


def upsert_features(conn: sqlite3.Connection, records: list[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    for r in records:
        cur.execute(
            """
            INSERT INTO google_trends_features (
                keyword, date, interest, interest_norm, rolling_avg_7d,
                pct_change_7d, zscore_30d, processed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(keyword, date) DO UPDATE SET
                interest=excluded.interest,
                interest_norm=excluded.interest_norm,
                rolling_avg_7d=excluded.rolling_avg_7d,
                pct_change_7d=excluded.pct_change_7d,
                zscore_30d=excluded.zscore_30d,
                processed_at=excluded.processed_at
            """,
            (
                r["keyword"], r["date"], r["interest"], r["interest_norm"],
                r["rolling_avg_7d"], r["pct_change_7d"], r["zscore_30d"], now,
            ),
        )
    conn.commit()


def upsert_common(conn: sqlite3.Connection, records: list[dict]) -> None:
    cur = conn.cursor()
    for r in records:
        cur.execute(
            """
            INSERT INTO google_trends_common (
                id, source, source_type, url, title, description, full_text,
                published_time_utc, ingestion_time_utc, country, region, language,
                asset_class, market, sector, event_type, importance_score,
                sentiment_score, confidence_score, keywords, named_entities,
                related_assets, raw_response
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                source=excluded.source,
                source_type=excluded.source_type,
                url=excluded.url,
                title=excluded.title,
                description=excluded.description,
                full_text=excluded.full_text,
                published_time_utc=excluded.published_time_utc,
                ingestion_time_utc=excluded.ingestion_time_utc,
                country=excluded.country,
                region=excluded.region,
                language=excluded.language,
                asset_class=excluded.asset_class,
                market=excluded.market,
                sector=excluded.sector,
                event_type=excluded.event_type,
                importance_score=excluded.importance_score,
                sentiment_score=excluded.sentiment_score,
                confidence_score=excluded.confidence_score,
                keywords=excluded.keywords,
                named_entities=excluded.named_entities,
                related_assets=excluded.related_assets,
                raw_response=excluded.raw_response
            """,
            (
                r["id"], r["source"], r["source_type"], r["url"], r["title"],
                r["description"], r["full_text"], r["published_time_utc"],
                r["ingestion_time_utc"], r["country"], r["region"], r["language"],
                r["asset_class"], r["market"], r["sector"], r["event_type"],
                r["importance_score"], r["sentiment_score"], r["confidence_score"],
                json.dumps(r["keywords"]), json.dumps(r["named_entities"]),
                json.dumps(r["related_assets"]),
                json.dumps(r["raw_response"], default=str) if r["raw_response"] is not None else None,
            ),
        )
    conn.commit()
