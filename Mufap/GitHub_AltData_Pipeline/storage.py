"""
storage.py — Stage 5: Data Storage

SQLite storage layer for the GitHub alt-data pipeline. Two tables:
  - github_raw      : what collect.py returned, one row per (repo, date,
                       metric). Whichever columns don't apply to a given
                       metric (e.g. stars/forks on a "commits" row) stay
                       NULL.
  - github_features : computed features (rolling avg, pct change,
                       z-score) from transform.py. Populated by
                       pipeline.py's run_once(): after upsert_raw(), the
                       pipeline reads back the full history via
                       get_raw_records(), computes features via
                       clean() + transform(), and writes the results
                       via upsert_features().

Mirrors ../Google trends/storage.py's upsert-on-conflict pattern so
repeated pipeline runs never duplicate rows.
"""

import json
import sqlite3
from datetime import datetime, timezone

DB_PATH = "github_data.db"


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS github_raw (
            repo       TEXT NOT NULL,
            date       TEXT NOT NULL,
            metric     TEXT NOT NULL,
            stars      INTEGER,
            forks      INTEGER,
            commits    INTEGER,
            is_partial INTEGER,
            fetched_at TEXT,
            PRIMARY KEY (repo, date, metric)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS github_features (
            repo         TEXT NOT NULL,
            date         TEXT NOT NULL,
            metric       TEXT NOT NULL,
            value        REAL,
            value_norm   REAL,
            rolling_avg  REAL,
            pct_change   REAL,
            zscore       REAL,
            processed_at TEXT,
            PRIMARY KEY (repo, date, metric)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS github_common (
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
            INSERT INTO github_raw (repo, date, metric, stars, forks, commits, is_partial, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo, date, metric) DO UPDATE SET
                stars=excluded.stars,
                forks=excluded.forks,
                commits=excluded.commits,
                is_partial=excluded.is_partial,
                fetched_at=excluded.fetched_at
            """,
            (
                r["repo"],
                r["date"],
                r["metric"],
                r.get("stars"),
                r.get("forks"),
                r.get("commits"),
                int(r["is_partial"]) if "is_partial" in r else None,
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
            INSERT INTO github_features (
                repo, date, metric, value, value_norm, rolling_avg,
                pct_change, zscore, processed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo, date, metric) DO UPDATE SET
                value=excluded.value,
                value_norm=excluded.value_norm,
                rolling_avg=excluded.rolling_avg,
                pct_change=excluded.pct_change,
                zscore=excluded.zscore,
                processed_at=excluded.processed_at
            """,
            (
                r["repo"],
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
    Read everything out of github_raw as plain dicts shaped like
    clean.py's RAW_COLUMNS (repo, date, metric, stars, forks, commits,
    is_partial) — no fetched_at, since nothing downstream uses it.

    Deliberately does no is_partial coercion here: it passes through
    whatever SQLite naturally returns (int 0/1), relying on clean.py's
    existing coercion (added specifically to make records read back
    out of the database safe to clean) to handle it. This is the
    integration path that fix was built for — pipeline.py needs the
    FULL raw history, not just a single day's fresh collect() output,
    to compute meaningful multi-week rolling/pct-change/z-score
    features.
    """
    cur = conn.execute(
        "SELECT repo, date, metric, stars, forks, commits, is_partial FROM github_raw"
    )
    columns = [d[0] for d in cur.description]
    return [dict(zip(columns, row)) for row in cur.fetchall()]


def upsert_common(conn: sqlite3.Connection, records: "list[dict]") -> None:
    cur = conn.cursor()
    for r in records:
        cur.execute(
            """
            INSERT INTO github_common (
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
