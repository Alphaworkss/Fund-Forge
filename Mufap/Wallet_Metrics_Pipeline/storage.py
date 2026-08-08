"""
storage.py — Stage 5: Data Storage

SQLite storage layer for the Blockchain Wallet Metrics pipeline. Two
tables:
  - wallet_metrics_raw      : what collect.py (or a coin adapter's
                                backfill()) returned, one row per
                                (coin, date, metric).
  - wallet_metrics_features : reserved for transform.py's output
                                (rolling avg, pct change, z-score).
                                Schema only for now — transform.py
                                doesn't exist yet (see
                                plan-clean-transform.md), so this
                                table stays empty until that plan is
                                implemented.

Mirrors ../GitHub/storage.py's upsert-on-conflict pattern so repeated
pipeline runs never duplicate rows.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parent / "wallet_metrics.db")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wallet_metrics_raw (
            coin       TEXT NOT NULL,
            date       TEXT NOT NULL,
            metric     TEXT NOT NULL,
            value      REAL,
            is_partial INTEGER,
            fetched_at TEXT,
            PRIMARY KEY (coin, date, metric)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wallet_metrics_features (
            coin         TEXT NOT NULL,
            date         TEXT NOT NULL,
            metric       TEXT NOT NULL,
            value        REAL,
            value_norm   REAL,
            rolling_avg  REAL,
            pct_change   REAL,
            zscore       REAL,
            processed_at TEXT,
            PRIMARY KEY (coin, date, metric)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wallet_metrics_common (
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


def upsert_raw(conn: sqlite3.Connection, records: "list[dict]") -> None:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    for r in records:
        cur.execute(
            """
            INSERT INTO wallet_metrics_raw (coin, date, metric, value, is_partial, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(coin, date, metric) DO UPDATE SET
                value=excluded.value,
                is_partial=excluded.is_partial,
                fetched_at=excluded.fetched_at
            """,
            (
                r["coin"],
                r["date"],
                r["metric"],
                r["value"],
                int(r["is_partial"]),
                now,
            ),
        )
    conn.commit()


def upsert_features(conn: sqlite3.Connection, records: "list[dict]") -> None:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    for r in records:
        cur.execute(
            """
            INSERT INTO wallet_metrics_features (
                coin, date, metric, value, value_norm, rolling_avg,
                pct_change, zscore, processed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(coin, date, metric) DO UPDATE SET
                value=excluded.value,
                value_norm=excluded.value_norm,
                rolling_avg=excluded.rolling_avg,
                pct_change=excluded.pct_change,
                zscore=excluded.zscore,
                processed_at=excluded.processed_at
            """,
            (
                r["coin"],
                r["date"],
                r["metric"],
                r["value"],
                r["value_norm"],
                r["rolling_avg"],
                r["pct_change"],
                r["zscore"],
                now,
            ),
        )
    conn.commit()


def get_raw_records(conn: sqlite3.Connection) -> "list[dict]":
    """
    Read everything out of wallet_metrics_raw as plain dicts shaped like
    clean.py's RAW_COLUMNS (coin, date, metric, value, is_partial) — no
    fetched_at, since nothing downstream uses it.

    pipeline.py needs the FULL raw history, not just a single day's
    fresh collect() output, to compute meaningful multi-week
    rolling/pct-change/z-score features.
    """
    cur = conn.execute(
        "SELECT coin, date, metric, value, is_partial FROM wallet_metrics_raw"
    )
    columns = [d[0] for d in cur.description]
    records = []
    for row in cur.fetchall():
        record = dict(zip(columns, row))
        # Convert SQLite integer back to boolean for clean.py compatibility
        record["is_partial"] = bool(record["is_partial"])
        records.append(record)
    return records


def upsert_common(conn: sqlite3.Connection, records: "list[dict]") -> None:
    cur = conn.cursor()
    for r in records:
        cur.execute(
            """
            INSERT INTO wallet_metrics_common (
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
