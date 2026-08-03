# Blockchain Wallet Metrics Pipeline — collect.py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `collect.py` for the Blockchain Wallet Metrics pipeline — a thin dispatcher over 3 per-coin adapters (`sources/bitcoin.py`, `sources/ethereum.py`, `sources/bnb.py`) that each expose `backfill(years=2)` and `collect()`, per the approved design in `design.md`. Ripple and Solana are explicitly out of scope for this plan (see `design.md`'s "Sources tracked" and "Open items for later stages") — do not add adapters for them here.

**Architecture:** Three adapter modules under `sources/`, one per coin, each returning the same long-format record shape (`coin, date, metric, value, is_partial`). Bitcoin talks to blockchain.com's Charts API (JSON, no key). Ethereum and BNB Chain both talk to their respective block explorer's public chart-CSV export (`?output=csv`, no key) via a small shared helper (`sources/_scan_csv.py`) — they're the same platform family (Etherscan/BscScan), so the fetch-and-parse mechanics are identical; only which charts exist per coin differs. `collect.py` itself loops over all 3 adapters' `collect()` with per-coin isolation, mirroring the GitHub pipeline's per-repo isolation.

**Tech Stack:** Python 3.12, `requests` (HTTP), stdlib `csv`/`io` (CSV parsing, no `pandas` needed at this stage), `pytest` + `unittest.mock` (testing, no real network calls).

## Global Constraints

- Project lives at `D:\news scrapper\Blockchain wallet metrics` — **not a git repo** (same situation as `..\GitHub`, verified the same way: `git status` there returns "not a git repository"). Every task below ends with a "Commit" step in the standard template; skip that step entirely here and just confirm tests pass. Do not run `git init` or any git command in this folder unless the user asks.
- **No API keys of any kind are needed for this plan.** All 3 in-scope coins use free, unauthenticated endpoints — confirmed live during Phase 1 research (see `design.md`). Do not add `os.environ` lookups for `ETHERSCAN_API_KEY`/`BSCSCAN_API_KEY` — they don't apply to the chart-CSV mechanism this plan uses.
- **`is_partial` is always `False`** for every record in this plan — verified live (see `design.md`'s "`collect.py` — two entry points" section: none of blockchain.com/Etherscan/BscScan publish an in-progress "today" row). Every adapter sets it explicitly to `False` rather than omitting it, for schema consistency with the sibling pipelines.
- Follow the file/style conventions already established in `..\GitHub\collect.py`: a module-level docstring explaining the stage, `logging` (not `print`) for diagnostics, private helpers prefixed with `_`.
- Reference implementation for the dispatcher's per-source-isolation pattern: `..\GitHub\collect.py` (already read in full during design) — this plan's `collect.py` adapts that per-repo isolation to per-coin.
- Real response shapes below (JSON from blockchain.com, CSV headers from Etherscan/BscScan) were captured via live `curl` requests during Phase 1 research on 2026-07-31 — not guessed. If a live shape ever changes, that's a real regression to investigate, not something this plan anticipated wrong.
- Scope: this plan covers `collect.py`, `sources/__init__.py`, `sources/_scan_csv.py`, `sources/bitcoin.py`, `sources/ethereum.py`, `sources/bnb.py`, `storage.py` (base schema + `upsert_raw`/`get_connection` only — matching the GitHub sibling's plan, which built its `storage.py` alongside `collect.py` too, before `clean.py`/`transform.py` existed), and `export_excel.py`. `clean.py`/`transform.py` and `storage.py`'s `upsert_features()` addition are covered by `plan-clean-transform.md`; `storage.py`'s `get_raw_records()` addition and `pipeline.py` are covered by `plan-pipeline.md` — do not create any of those here.

---

### Task 1: Bitcoin adapter (`sources/bitcoin.py`)

**Files:**
- Create: `D:\news scrapper\Blockchain wallet metrics\sources\__init__.py` (empty — makes `sources` a package)
- Create: `D:\news scrapper\Blockchain wallet metrics\sources\bitcoin.py`
- Test: `D:\news scrapper\Blockchain wallet metrics\test_collect_bitcoin.py`

**Interfaces:**
- Produces: `sources.bitcoin.backfill(years: int = 2) -> list[dict]`, `sources.bitcoin.collect() -> list[dict]`. Both return records shaped `{"coin": "bitcoin", "date": "YYYY-MM-DD", "metric": str, "value": float, "is_partial": False}`, `metric ∈ {"active_addresses", "tx_count", "tx_volume"}`. Task 4's `collect.py` dispatcher calls `collect()` directly.

- [ ] **Step 1: Write the failing tests**

```python
# test_collect_bitcoin.py
"""
test_collect_bitcoin.py — Stage 8: Testing (sources/bitcoin.py)

Mocks requests.get so these tests never touch the network or the real
blockchain.com API. Run with: pytest test_collect_bitcoin.py
"""

from unittest.mock import Mock, patch

from sources import bitcoin


def _fake_response(status_code=200, json_data=None):
    resp = Mock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else {}
    return resp


SAMPLE_VALUES = [
    {"x": 1785283200, "y": 478468.0},  # 2026-07-29 (UTC)
    {"x": 1785369600, "y": 497475.0},  # 2026-07-30 (UTC)
]


@patch("sources.bitcoin.requests.get")
def test_fetch_chart_returns_values_on_ok_status(mock_get):
    mock_get.return_value = _fake_response(
        json_data={"status": "ok", "values": SAMPLE_VALUES}
    )

    values = bitcoin._fetch_chart("n-unique-addresses", "10days")

    assert values == SAMPLE_VALUES


@patch("sources.bitcoin.requests.get")
def test_fetch_chart_returns_none_on_non_200(mock_get):
    mock_get.return_value = _fake_response(status_code=404)

    values = bitcoin._fetch_chart("n-unique-addresses", "10days")

    assert values is None


@patch("sources.bitcoin.requests.get")
def test_fetch_chart_returns_none_on_non_ok_status(mock_get):
    mock_get.return_value = _fake_response(json_data={"status": "error"})

    values = bitcoin._fetch_chart("n-unique-addresses", "10days")

    assert values is None


def test_values_to_records_shape():
    records = bitcoin._values_to_records("active_addresses", SAMPLE_VALUES)

    assert records == [
        {"coin": "bitcoin", "date": "2026-07-29", "metric": "active_addresses", "value": 478468.0, "is_partial": False},
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "active_addresses", "value": 497475.0, "is_partial": False},
    ]


@patch("sources.bitcoin._fetch_chart")
def test_backfill_requests_all_three_metrics_with_years_timespan(mock_fetch):
    mock_fetch.return_value = SAMPLE_VALUES

    bitcoin.backfill(years=2)

    called_charts = {call.args[0] for call in mock_fetch.call_args_list}
    assert called_charts == {"n-unique-addresses", "n-transactions", "estimated-transaction-volume"}
    for call in mock_fetch.call_args_list:
        assert call.args[1] == "2years"


@patch("sources.bitcoin._fetch_chart")
def test_backfill_returns_records_for_all_metrics(mock_fetch):
    mock_fetch.return_value = SAMPLE_VALUES

    records = bitcoin.backfill(years=2)

    assert len(records) == 6  # 2 values x 3 metrics
    assert {r["metric"] for r in records} == {"active_addresses", "tx_count", "tx_volume"}


@patch("sources.bitcoin._fetch_chart")
def test_backfill_skips_a_failed_metric_without_crashing(mock_fetch):
    def side_effect(chart, timespan):
        return None if chart == "n-transactions" else SAMPLE_VALUES

    mock_fetch.side_effect = side_effect

    records = bitcoin.backfill(years=2)

    assert "tx_count" not in {r["metric"] for r in records}
    assert len(records) == 4  # 2 values x remaining 2 metrics


@patch("sources.bitcoin._fetch_chart")
def test_collect_uses_10days_timespan(mock_fetch):
    mock_fetch.return_value = SAMPLE_VALUES

    bitcoin.collect()

    for call in mock_fetch.call_args_list:
        assert call.args[1] == "10days"


@patch("sources.bitcoin._fetch_chart")
def test_collect_records_are_never_partial(mock_fetch):
    mock_fetch.return_value = SAMPLE_VALUES

    records = bitcoin.collect()

    assert all(r["is_partial"] is False for r in records)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_collect_bitcoin.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sources'` (package doesn't exist yet).

- [ ] **Step 3: Write minimal implementation**

```python
# sources/__init__.py
# (intentionally empty — makes `sources` a package)
```

```python
# sources/bitcoin.py
"""
sources/bitcoin.py — Bitcoin adapter (blockchain.com Charts API)

No API key required. Live-verified 2026-07-31:
  GET https://api.blockchain.info/charts/{chart}?timespan=...&format=json
returns {"status": "ok", ..., "values": [{"x": unix_ts, "y": value}, ...]}.

The API never publishes an in-progress "today" row — the most recent
value is always for the prior, fully-finalized day (verified live by
comparing the latest returned date against the actual current date) —
so every record this module returns has is_partial=False. See
design.md's "collect.py — two entry points" section.
"""

import datetime
import logging

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.blockchain.info/charts"

CHARTS = {
    "active_addresses": "n-unique-addresses",
    "tx_count": "n-transactions",
    "tx_volume": "estimated-transaction-volume",
}


def _fetch_chart(chart: str, timespan: str) -> "list[dict] | None":
    """
    Returns the chart's `values` list ([{"x": unix_ts, "y": value}, ...])
    on success, or None on any failure (network error, non-200, or a
    non-"ok" status in the response body) after logging why — lets
    callers skip a single failed metric without crashing the whole run.
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/{chart}",
            params={"timespan": timespan, "format": "json"},
            timeout=10,
        )
    except requests.RequestException:
        logger.exception("Request failed for chart %s", chart)
        return None

    if resp.status_code != 200:
        logger.warning("Chart %s request failed: HTTP %s", chart, resp.status_code)
        return None

    data = resp.json()
    if data.get("status") != "ok":
        logger.warning("Chart %s returned non-ok status: %s", chart, data.get("status"))
        return None

    return data["values"]


def _values_to_records(metric: str, values: "list[dict]") -> "list[dict]":
    records = []
    for point in values:
        date = datetime.datetime.fromtimestamp(point["x"], tz=datetime.timezone.utc).date().isoformat()
        records.append(
            {"coin": "bitcoin", "date": date, "metric": metric, "value": point["y"], "is_partial": False}
        )
    return records


def backfill(years: int = 2) -> "list[dict]":
    """One-time historical fetch: all 3 metrics, back `years` years."""
    timespan = f"{years}years"
    records = []
    for metric, chart in CHARTS.items():
        values = _fetch_chart(chart, timespan)
        if values is None:
            logger.warning("Skipping metric %s for bitcoin: chart fetch failed", metric)
            continue
        records.extend(_values_to_records(metric, values))
    return records


def collect() -> "list[dict]":
    """
    Daily run: last 10 days for all 3 metrics, to pick up whichever day
    most recently finished publishing plus catch any late revisions.
    """
    records = []
    for metric, chart in CHARTS.items():
        values = _fetch_chart(chart, "10days")
        if values is None:
            logger.warning("Skipping metric %s for bitcoin: chart fetch failed", metric)
            continue
        records.extend(_values_to_records(metric, values))
    return records
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_collect_bitcoin.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: No git repo — skip commit (see Global Constraints). Confirm the files are saved and move to Task 2.**

---

### Task 2: Shared CSV helper + Ethereum adapter (`sources/_scan_csv.py`, `sources/ethereum.py`)

**Files:**
- Create: `D:\news scrapper\Blockchain wallet metrics\sources\_scan_csv.py`
- Create: `D:\news scrapper\Blockchain wallet metrics\sources\ethereum.py`
- Test: `D:\news scrapper\Blockchain wallet metrics\test_collect_ethereum.py`

**Interfaces:**
- Produces: `sources._scan_csv.fetch_csv(url: str) -> list[dict] | None` (parsed CSV rows as dicts, keyed by header). `sources.ethereum.backfill(years: int = 2) -> list[dict]`, `sources.ethereum.collect() -> list[dict]`, same record shape as Task 1 (`coin="ethereum"`, `metric ∈ {"active_addresses", "tx_count"}` — no `tx_volume`, see `design.md`). Task 3's `sources/bnb.py` also consumes `fetch_csv` directly. Task 4's `collect.py` dispatcher calls `ethereum.collect()`.

- [ ] **Step 1: Write the failing tests**

```python
# test_collect_ethereum.py
"""
test_collect_ethereum.py — Stage 8: Testing (sources/ethereum.py)

Mocks requests.get so these tests never touch the network or the real
Etherscan site. Run with: pytest test_collect_ethereum.py
"""

from unittest.mock import Mock, patch

from sources import ethereum
from sources._scan_csv import fetch_csv

TX_CSV = (
    '"Date(UTC)","UnixTimeStamp","Value"\r\n'
    '"7/29/2026","1785283200","1734060"\r\n'
    '"7/30/2026","1785369600","1766208"\r\n'
)

ACTIVE_ADDRESS_CSV = (
    '"Date(UTC)","Unique Address Total Count","Unique Address Receive Count","Unique Address Sent Count"\r\n'
    '"07/29/2026","478468","300000","178468"\r\n'
    '"07/30/2026","497475","310000","187475"\r\n'
)


def _fake_response(status_code=200, text=""):
    resp = Mock()
    resp.status_code = status_code
    resp.text = text
    return resp


@patch("sources._scan_csv.requests.get")
def test_fetch_csv_parses_rows_into_dicts(mock_get):
    mock_get.return_value = _fake_response(text=TX_CSV)

    rows = fetch_csv("https://etherscan.io/chart/tx?output=csv")

    assert rows == [
        {"Date(UTC)": "7/29/2026", "UnixTimeStamp": "1785283200", "Value": "1734060"},
        {"Date(UTC)": "7/30/2026", "UnixTimeStamp": "1785369600", "Value": "1766208"},
    ]


@patch("sources._scan_csv.requests.get")
def test_fetch_csv_returns_none_on_non_200(mock_get):
    mock_get.return_value = _fake_response(status_code=404)

    rows = fetch_csv("https://etherscan.io/chart/tx?output=csv")

    assert rows is None


@patch("sources.ethereum.fetch_csv")
def test_collect_returns_tx_count_and_active_addresses(mock_fetch_csv):
    def side_effect(url):
        if "active-address" in url:
            return list(__import__("csv").DictReader(ACTIVE_ADDRESS_CSV.splitlines()))
        return list(__import__("csv").DictReader(TX_CSV.splitlines()))

    mock_fetch_csv.side_effect = side_effect

    records = ethereum.collect()

    metrics = {r["metric"] for r in records}
    assert metrics == {"tx_count", "active_addresses"}
    assert all(r["coin"] == "ethereum" for r in records)
    assert all(r["is_partial"] is False for r in records)


@patch("sources.ethereum.fetch_csv")
def test_collect_tx_count_values_parsed_as_int(mock_fetch_csv):
    def side_effect(url):
        if "active-address" in url:
            return list(__import__("csv").DictReader(ACTIVE_ADDRESS_CSV.splitlines()))
        return list(__import__("csv").DictReader(TX_CSV.splitlines()))

    mock_fetch_csv.side_effect = side_effect

    records = ethereum.collect()

    tx_row = next(r for r in records if r["metric"] == "tx_count" and r["date"] == "2026-07-30")
    assert tx_row["value"] == 1766208
    assert isinstance(tx_row["value"], int)


@patch("sources.ethereum.fetch_csv")
def test_collect_active_address_uses_total_count_column(mock_fetch_csv):
    def side_effect(url):
        if "active-address" in url:
            return list(__import__("csv").DictReader(ACTIVE_ADDRESS_CSV.splitlines()))
        return list(__import__("csv").DictReader(TX_CSV.splitlines()))

    mock_fetch_csv.side_effect = side_effect

    records = ethereum.collect()

    addr_row = next(r for r in records if r["metric"] == "active_addresses" and r["date"] == "2026-07-30")
    assert addr_row["value"] == 497475


@patch("sources.ethereum.fetch_csv")
def test_collect_skips_metric_when_its_csv_fetch_fails(mock_fetch_csv):
    def side_effect(url):
        if "active-address" in url:
            return None
        return list(__import__("csv").DictReader(TX_CSV.splitlines()))

    mock_fetch_csv.side_effect = side_effect

    records = ethereum.collect()

    assert {r["metric"] for r in records} == {"tx_count"}


@patch("sources.ethereum.fetch_csv")
def test_backfill_filters_to_years_cutoff(mock_fetch_csv):
    old_tx_csv = (
        '"Date(UTC)","UnixTimeStamp","Value"\r\n'
        '"1/1/2015","1420070400","100"\r\n'
        '"7/30/2026","1785369600","1766208"\r\n'
    )

    def side_effect(url):
        if "active-address" in url:
            return []
        return list(__import__("csv").DictReader(old_tx_csv.splitlines()))

    mock_fetch_csv.side_effect = side_effect

    records = ethereum.backfill(years=2)

    dates = {r["date"] for r in records}
    assert "2015-01-01" not in dates
    assert "2026-07-30" in dates
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_collect_ethereum.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sources._scan_csv'`

- [ ] **Step 3: Write minimal implementation**

```python
# sources/_scan_csv.py
"""
sources/_scan_csv.py — shared CSV-chart fetch helper for Etherscan-
family block explorers (Etherscan, BscScan — same underlying platform,
same free, unauthenticated `?output=csv` chart-export mechanism).

Not a coin adapter itself — sources/ethereum.py and sources/bnb.py
both import fetch_csv() from here to avoid duplicating this logic.
"""

import csv
import io
import logging

import requests

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (FundForge alt-data pipeline)"}


def fetch_csv(url: str) -> "list[dict] | None":
    """
    GETs `url` (a chart page's ?output=csv export) and parses it into a
    list of dicts keyed by the CSV's header row. Returns None on any
    failure (network error or non-200) after logging why.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException:
        logger.exception("Request failed: %s", url)
        return None

    if resp.status_code != 200:
        logger.warning("Request to %s failed: HTTP %s", url, resp.status_code)
        return None

    return list(csv.DictReader(io.StringIO(resp.text)))
```

```python
# sources/ethereum.py
"""
sources/ethereum.py — Ethereum adapter (Etherscan chart CSV export)

No API key required. Etherscan's documented Stats API
(module=stats&action=dailytx/dailynewaddress) is Pro-only — confirmed
via docs.etherscan.io: "This is a PRO endpoint, available to the
Standard Plan and above." Instead, this uses Etherscan's public chart
pages' free, unauthenticated `?output=csv` export (the same mechanism
a signed-out browser uses) — live-verified 2026-07-31.

Only active_addresses and tx_count are collected. No tx_volume chart
exists on Etherscan (its chart index was enumerated directly — no
"ETH transferred"/volume chart is listed) — see design.md.
"""

import datetime
import logging

from sources._scan_csv import fetch_csv

logger = logging.getLogger(__name__)

TX_URL = "https://etherscan.io/chart/tx?output=csv"
ACTIVE_ADDRESS_URL = "https://etherscan.io/chart/active-address?output=csv"


def _parse_date(raw: str) -> str:
    return datetime.datetime.strptime(raw, "%m/%d/%Y").date().isoformat()


def _parse_tx_rows(rows: "list[dict]") -> "list[dict]":
    return [
        {
            "coin": "ethereum",
            "date": _parse_date(row["Date(UTC)"]),
            "metric": "tx_count",
            "value": int(row["Value"]),
            "is_partial": False,
        }
        for row in rows
    ]


def _parse_active_address_rows(rows: "list[dict]") -> "list[dict]":
    return [
        {
            "coin": "ethereum",
            "date": _parse_date(row["Date(UTC)"]),
            "metric": "active_addresses",
            "value": int(row["Unique Address Total Count"]),
            "is_partial": False,
        }
        for row in rows
    ]


def _collect_all() -> "list[dict]":
    records = []

    tx_rows = fetch_csv(TX_URL)
    if tx_rows is None:
        logger.warning("Skipping tx_count for ethereum: CSV fetch failed")
    else:
        records.extend(_parse_tx_rows(tx_rows))

    addr_rows = fetch_csv(ACTIVE_ADDRESS_URL)
    if addr_rows is None:
        logger.warning("Skipping active_addresses for ethereum: CSV fetch failed")
    else:
        records.extend(_parse_active_address_rows(addr_rows))

    return records


def backfill(years: int = 2) -> "list[dict]":
    """
    Etherscan's chart CSV always returns the complete history (back to
    2015-07-30, verified live) — there's no server-side "last N years"
    filter. `years` is applied as a local post-filter so storage
    doesn't hold more raw rows than intended.
    """
    all_records = _collect_all()
    cutoff = (datetime.date.today() - datetime.timedelta(days=365 * years)).isoformat()
    return [r for r in all_records if r["date"] >= cutoff]


def collect() -> "list[dict]":
    """
    Same CSV endpoints as backfill() — Etherscan doesn't offer a
    filtered "just the last N days" export, so this re-downloads the
    full CSV every day. One cheap request per metric either way; the
    storage layer's upsert absorbs the redundancy for free.
    """
    return _collect_all()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_collect_ethereum.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the files are saved and move to Task 3.**

---

### Task 3: BNB Chain adapter (`sources/bnb.py`)

**Files:**
- Create: `D:\news scrapper\Blockchain wallet metrics\sources\bnb.py`
- Test: `D:\news scrapper\Blockchain wallet metrics\test_collect_bnb.py`

**Interfaces:**
- Consumes: `sources._scan_csv.fetch_csv(url) -> list[dict] | None` from Task 2.
- Produces: `sources.bnb.backfill(years: int = 2) -> list[dict]`, `sources.bnb.collect() -> list[dict]`, records shaped `{"coin": "bnb", "date": "YYYY-MM-DD", "metric": "tx_count", "value": int, "is_partial": False}` — **`tx_count` only**, no `active_addresses`/`tx_volume` (see `design.md` — BscScan has no active-address chart and no volume chart). Task 4's `collect.py` dispatcher calls `collect()`.

- [ ] **Step 1: Write the failing tests**

```python
# test_collect_bnb.py
"""
test_collect_bnb.py — Stage 8: Testing (sources/bnb.py)

Mocks fetch_csv so these tests never touch the network or the real
BscScan site. Run with: pytest test_collect_bnb.py
"""

import csv
from unittest.mock import patch

from sources import bnb

TX_CSV_ROWS = [
    {"Date(UTC)": "7/29/2026", "UnixTimeStamp": "1785283200", "Value": "15520165"},
    {"Date(UTC)": "7/30/2026", "UnixTimeStamp": "1785369600", "Value": "16323969"},
]


@patch("sources.bnb.fetch_csv")
def test_collect_returns_tx_count_only(mock_fetch_csv):
    mock_fetch_csv.return_value = TX_CSV_ROWS

    records = bnb.collect()

    assert {r["metric"] for r in records} == {"tx_count"}
    assert all(r["coin"] == "bnb" for r in records)


@patch("sources.bnb.fetch_csv")
def test_collect_parses_date_and_value(mock_fetch_csv):
    mock_fetch_csv.return_value = TX_CSV_ROWS

    records = bnb.collect()

    row = next(r for r in records if r["date"] == "2026-07-30")
    assert row["value"] == 16323969
    assert isinstance(row["value"], int)
    assert row["is_partial"] is False


@patch("sources.bnb.fetch_csv")
def test_collect_returns_empty_list_when_fetch_fails(mock_fetch_csv):
    mock_fetch_csv.return_value = None

    records = bnb.collect()

    assert records == []


@patch("sources.bnb.fetch_csv")
def test_backfill_filters_to_years_cutoff(mock_fetch_csv):
    mock_fetch_csv.return_value = [
        {"Date(UTC)": "8/29/2020", "UnixTimeStamp": "1598659200", "Value": "122"},
        {"Date(UTC)": "7/30/2026", "UnixTimeStamp": "1785369600", "Value": "16323969"},
    ]

    records = bnb.backfill(years=2)

    dates = {r["date"] for r in records}
    assert "2020-08-29" not in dates
    assert "2026-07-30" in dates


@patch("sources.bnb.fetch_csv")
def test_backfill_calls_fetch_csv_with_bnb_tx_chart_url(mock_fetch_csv):
    mock_fetch_csv.return_value = TX_CSV_ROWS

    bnb.backfill(years=2)

    mock_fetch_csv.assert_called_once_with("https://bscscan.com/chart/tx?output=csv")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_collect_bnb.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sources.bnb'`

- [ ] **Step 3: Write minimal implementation**

```python
# sources/bnb.py
"""
sources/bnb.py — BNB Chain adapter (BscScan chart CSV export)

No API key required — same free chart-CSV mechanism as
sources/ethereum.py (BscScan is the same platform family as
Etherscan). Live-verified 2026-07-31:
https://bscscan.com/chart/tx?output=csv works identically to
Etherscan's, data starting 2020-08-29 (BSC's effective launch).

Only tx_count is collected. BscScan has no active-address chart at
all (unlike Etherscan) and no tx_volume chart either — its chart index
(bscscan.com/charts) was enumerated directly and neither exists. Do
not add those metrics here without a real confirmed source first —
see design.md's "Sources tracked" for what was actually checked.
"""

import datetime
import logging

from sources._scan_csv import fetch_csv

logger = logging.getLogger(__name__)

TX_URL = "https://bscscan.com/chart/tx?output=csv"


def _parse_date(raw: str) -> str:
    return datetime.datetime.strptime(raw, "%m/%d/%Y").date().isoformat()


def _parse_tx_rows(rows: "list[dict]") -> "list[dict]":
    return [
        {
            "coin": "bnb",
            "date": _parse_date(row["Date(UTC)"]),
            "metric": "tx_count",
            "value": int(row["Value"]),
            "is_partial": False,
        }
        for row in rows
    ]


def backfill(years: int = 2) -> "list[dict]":
    """
    BscScan's chart CSV always returns the complete history (back to
    2020-08-29) — no server-side "last N years" filter, same as
    Ethereum. `years` is applied as a local post-filter.
    """
    rows = fetch_csv(TX_URL)
    if rows is None:
        logger.warning("Skipping tx_count for bnb: CSV fetch failed")
        return []
    records = _parse_tx_rows(rows)
    cutoff = (datetime.date.today() - datetime.timedelta(days=365 * years)).isoformat()
    return [r for r in records if r["date"] >= cutoff]


def collect() -> "list[dict]":
    """Same CSV endpoint as backfill() — re-downloads the full CSV; the storage layer's upsert absorbs the redundancy."""
    rows = fetch_csv(TX_URL)
    if rows is None:
        logger.warning("Skipping tx_count for bnb: CSV fetch failed")
        return []
    return _parse_tx_rows(rows)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_collect_bnb.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the files are saved and move to Task 4.**

---

### Task 4: Dispatcher (`collect.py`)

**Files:**
- Create: `D:\news scrapper\Blockchain wallet metrics\collect.py`
- Test: `D:\news scrapper\Blockchain wallet metrics\test_collect.py`

**Interfaces:**
- Consumes: `sources.bitcoin.collect()`, `sources.ethereum.collect()`, `sources.bnb.collect()` from Tasks 1-3.
- Produces: `collect() -> list[dict]` (all 3 coins' records combined), `ADAPTERS: dict[str, module]`. `plan-pipeline.md`'s `pipeline.py` (a later plan) calls this directly.

- [ ] **Step 1: Write the failing tests**

```python
# test_collect.py
"""
test_collect.py — Stage 8: Testing (collect.py dispatcher)

Patches each coin's ADAPTERS entry directly (not the network) — this
module's own tests never touch sources/*.py's real HTTP calls; that's
covered by test_collect_bitcoin.py/test_collect_ethereum.py/
test_collect_bnb.py individually. Run with: pytest test_collect.py
"""

from unittest.mock import MagicMock, patch

import collect


def _fake_adapter(records):
    adapter = MagicMock()
    adapter.collect.return_value = records
    return adapter


def test_collect_combines_records_from_all_adapters():
    fake_adapters = {
        "bitcoin": _fake_adapter([{"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 1, "is_partial": False}]),
        "ethereum": _fake_adapter([{"coin": "ethereum", "date": "2026-07-30", "metric": "tx_count", "value": 2, "is_partial": False}]),
        "bnb": _fake_adapter([{"coin": "bnb", "date": "2026-07-30", "metric": "tx_count", "value": 3, "is_partial": False}]),
    }

    with patch.dict(collect.ADAPTERS, fake_adapters, clear=True):
        records = collect.collect()

    assert {r["coin"] for r in records} == {"bitcoin", "ethereum", "bnb"}
    assert len(records) == 3


def test_collect_skips_a_coin_whose_adapter_raises():
    failing_adapter = MagicMock()
    failing_adapter.collect.side_effect = RuntimeError("boom")
    fake_adapters = {
        "bitcoin": failing_adapter,
        "ethereum": _fake_adapter([{"coin": "ethereum", "date": "2026-07-30", "metric": "tx_count", "value": 2, "is_partial": False}]),
        "bnb": _fake_adapter([{"coin": "bnb", "date": "2026-07-30", "metric": "tx_count", "value": 3, "is_partial": False}]),
    }

    with patch.dict(collect.ADAPTERS, fake_adapters, clear=True):
        records = collect.collect()

    assert {r["coin"] for r in records} == {"ethereum", "bnb"}


def test_collect_skips_a_coin_that_returns_no_records():
    fake_adapters = {
        "bitcoin": _fake_adapter([]),
        "ethereum": _fake_adapter([{"coin": "ethereum", "date": "2026-07-30", "metric": "tx_count", "value": 2, "is_partial": False}]),
        "bnb": _fake_adapter([{"coin": "bnb", "date": "2026-07-30", "metric": "tx_count", "value": 3, "is_partial": False}]),
    }

    with patch.dict(collect.ADAPTERS, fake_adapters, clear=True):
        records = collect.collect()

    assert {r["coin"] for r in records} == {"ethereum", "bnb"}


def test_collect_returns_empty_list_when_every_adapter_fails():
    fake_adapters = {
        "bitcoin": _fake_adapter([]),
        "ethereum": _fake_adapter([]),
        "bnb": _fake_adapter([]),
    }

    with patch.dict(collect.ADAPTERS, fake_adapters, clear=True):
        records = collect.collect()

    assert records == []


def test_adapters_dict_has_exactly_the_three_in_scope_coins():
    assert set(collect.ADAPTERS.keys()) == {"bitcoin", "ethereum", "bnb"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_collect.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'collect'` (file doesn't exist yet).

- [ ] **Step 3: Write minimal implementation**

```python
# collect.py
"""
collect.py — Stage 1: Data Collection (dispatcher)

Loops over each in-scope coin's sources/ adapter, calling collect() on
each. Per-coin isolation: an adapter that raises, or returns no
records, logs a warning and is skipped — a failing coin never blocks
the others. Mirrors ../GitHub/collect.py's per-repo isolation.

Only collect() is dispatched here. backfill() is never called
automatically for any coin — same reasoning as GitHub's
backfill_commit_history(): a scheduled daily job unexpectedly making a
slow historical pull the first time it hits an empty table would be a
surprising failure mode. Each coin's backfill() is run once, by hand,
before daily runs start (see README.md).

Ripple and Solana are not in ADAPTERS — see design.md's "Sources
tracked" for why both are deferred to a follow-up phase.
"""

import logging

from sources import bitcoin, bnb, ethereum

logger = logging.getLogger(__name__)

ADAPTERS = {
    "bitcoin": bitcoin,
    "ethereum": ethereum,
    "bnb": bnb,
}


def collect() -> "list[dict]":
    records = []
    for coin, adapter in ADAPTERS.items():
        try:
            coin_records = adapter.collect()
        except Exception:
            logger.exception("Adapter for %s raised an unexpected error — skipping", coin)
            continue

        if not coin_records:
            logger.warning("No records collected for %s", coin)
            continue

        records.extend(coin_records)

    return records
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_collect.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the file is saved and move to Task 5.**

---

### Task 5: SQLite storage (`storage.py`)

**Files:**
- Create: `D:\news scrapper\Blockchain wallet metrics\storage.py`
- Create: `D:\news scrapper\Blockchain wallet metrics\test_storage.py`

**Interfaces:**
- Consumes: record dicts shaped like Tasks 1-4's output (`coin`, `date`, `metric`, `value`, `is_partial`).
- Produces: `get_connection(db_path: str = DB_PATH) -> sqlite3.Connection`, `upsert_raw(conn, records: list[dict]) -> None`. `plan-clean-transform.md`'s Task 3 (`upsert_features`) and `plan-pipeline.md`'s `pipeline.py` both build on this file. Task 6's `export_excel.py` and Task 7's `README.md` both read from the `wallet_metrics_raw`/`wallet_metrics_features` tables this creates.

- [ ] **Step 1: Write the failing tests**

```python
# test_storage.py
"""
test_storage.py — Stage 8: Testing (storage.py)

Run with: pytest test_storage.py
"""

from storage import get_connection, upsert_raw


def test_upsert_raw_is_idempotent():
    conn = get_connection(":memory:")
    records = [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False}
    ]

    upsert_raw(conn, records)
    upsert_raw(conn, records)

    count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_raw").fetchone()[0]
    assert count == 1
    conn.close()


def test_upsert_raw_updates_existing_row_on_conflict():
    conn = get_connection(":memory:")
    upsert_raw(conn, [{"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 700000, "is_partial": True}])
    upsert_raw(conn, [{"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False}])

    row = conn.execute("SELECT value, is_partial FROM wallet_metrics_raw").fetchone()

    assert row == (712078, 0)
    conn.close()


def test_upsert_raw_stores_multiple_metrics_and_coins_together():
    conn = get_connection(":memory:")

    upsert_raw(
        conn,
        [
            {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
            {"coin": "ethereum", "date": "2026-07-30", "metric": "active_addresses", "value": 497475, "is_partial": False},
        ],
    )

    count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_raw").fetchone()[0]
    assert count == 2
    conn.close()


def test_features_table_exists_but_starts_empty():
    conn = get_connection(":memory:")

    count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_features").fetchone()[0]

    assert count == 0
    conn.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_storage.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'storage'`

- [ ] **Step 3: Write minimal implementation**

```python
# storage.py
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

import sqlite3
from datetime import datetime, timezone

DB_PATH = "wallet_metrics.db"


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_storage.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the file is saved and move to Task 6.**

---

### Task 6: Excel export (`export_excel.py`)

**Files:**
- Create: `D:\news scrapper\Blockchain wallet metrics\export_excel.py`
- Create: `D:\news scrapper\Blockchain wallet metrics\test_export.py`

**Interfaces:**
- Consumes: `get_connection`, `upsert_raw` from Task 5.
- Produces: `export_to_excel(conn: sqlite3.Connection, excel_path: str = EXCEL_PATH) -> None`. Task 7's `README.md` documents running this after a collection run; `plan-pipeline.md`'s `pipeline.py` calls this at the end of `run_once()`.

- [ ] **Step 1: Write the failing test**

```python
# test_export.py
"""
test_export.py — Stage 8: Testing (export_excel.py)

Run with: pytest test_export.py
"""

import pandas as pd

from storage import get_connection, upsert_raw
from export_excel import export_to_excel


def test_export_writes_raw_and_features_sheets(tmp_path):
    conn = get_connection(":memory:")
    upsert_raw(
        conn,
        [{"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False}],
    )
    out_path = tmp_path / "out.xlsx"

    export_to_excel(conn, excel_path=str(out_path))

    assert out_path.exists()
    raw = pd.read_excel(out_path, sheet_name="raw")
    assert len(raw) == 1
    features = pd.read_excel(out_path, sheet_name="features")
    assert len(features) == 0
    conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest test_export.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'export_excel'`

- [ ] **Step 3: Write minimal implementation**

```python
# export_excel.py
"""
export_excel.py — Excel export

Exports the current contents of the wallet-metrics database to an
Excel workbook (wallet_metrics.xlsx by default) — one sheet per table
— for anyone on the team who'd rather look at a spreadsheet than query
SQLite directly.

Same design choice as ../GitHub/export_excel.py: regenerates the whole
file from SQLite on every run rather than merging into an existing
.xlsx — SQLite already handles dedup/upserts (see storage.py).

IMPORTANT: close wallet_metrics.xlsx in Excel before running this —
Excel locks the file while it's open, and writing to it will raise
PermissionError.
"""

import logging
import sqlite3

import pandas as pd

logger = logging.getLogger(__name__)

EXCEL_PATH = "wallet_metrics.xlsx"


def export_to_excel(conn: sqlite3.Connection, excel_path: str = EXCEL_PATH) -> None:
    raw_df = pd.read_sql_query("SELECT * FROM wallet_metrics_raw ORDER BY coin, date, metric", conn)
    features_df = pd.read_sql_query(
        "SELECT * FROM wallet_metrics_features ORDER BY coin, date, metric", conn
    )

    try:
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            raw_df.to_excel(writer, sheet_name="raw", index=False)
            features_df.to_excel(writer, sheet_name="features", index=False)
        logger.info("Exported %d raw rows to %s", len(raw_df), excel_path)
    except PermissionError:
        logger.error(
            "Could not write %s — it's probably still open in Excel. Close it and re-run.",
            excel_path,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest test_export.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: No git repo — skip commit. Confirm the file is saved and move to Task 7.**

---

### Task 7: Dependencies + README

**Files:**
- Create: `D:\news scrapper\Blockchain wallet metrics\requirements.txt`
- Create: `D:\news scrapper\Blockchain wallet metrics\README.md`

**Interfaces:**
- Consumes: everything from Tasks 1-6 (documents how to install and run backfill/collect/storage/export manually per coin).
- Produces: nothing further consumes this — it's the last task in this plan.

- [ ] **Step 1: Create `requirements.txt`**

```
requests
pandas
openpyxl
pytest
```

(`pandas`/`openpyxl` aren't used by this plan's own files, but are included now since `plan-clean-transform.md` and `plan-pipeline.md` need them immediately after — matches `..\GitHub\requirements.txt`'s shape.)

- [ ] **Step 2: Verify dependencies install cleanly**

Run: `pip install -r requirements.txt`
Expected: all four packages install (or report already satisfied) with no errors.

- [ ] **Step 3: Write `README.md`**

```markdown
# Blockchain Wallet Metrics Pipeline — Member 11 (FundForge)

Tracks on-chain wallet activity (active addresses, transaction count,
transaction volume) for major blockchains, as a proxy for real
economic/ecosystem activity. Pairs with the GitHub pipeline's
developer-activity signal for the same blockchain theme. See
`design.md` for the full design rationale (why coverage isn't uniform
across coins, and why Ripple/Solana are deferred), `CLAUDE.md` for
project conventions, and `PHASES.md` for build status.

**Status:** `collect.py`, its 3 coin adapters (`sources/bitcoin.py`,
`sources/ethereum.py`, `sources/bnb.py`), `storage.py` (raw storage
only), and `export_excel.py` are implemented and tested.
`clean.py`/`transform.py`/`storage.py`'s `upsert_features()` (see
`plan-clean-transform.md`) and `pipeline.py` (see `plan-pipeline.md`)
are not yet built — see `PHASES.md`.

**Coin coverage (not uniform — see `design.md`):**

| Coin | `active_addresses` | `tx_count` | `tx_volume` |
|---|---|---|---|
| Bitcoin | yes | yes | yes |
| Ethereum | yes | yes | no |
| BNB Chain | no | yes | no |

Ripple and Solana are not implemented yet — no confirmed free data
source (see `design.md`'s "Open items for later stages").

## Setup

```bash
pip install -r requirements.txt
```

No API keys or environment variables are needed — every source this
pipeline uses is free and unauthenticated.

## Running

**One-time historical backfill (run this first, once):**

```python
from sources import bitcoin, ethereum, bnb
from storage import get_connection, upsert_raw

conn = get_connection()
all_records = bitcoin.backfill() + ethereum.backfill() + bnb.backfill()
upsert_raw(conn, all_records)
conn.close()
```

**Daily collection (what the eventual scheduled task will call):**

```python
from collect import collect
from storage import get_connection, upsert_raw

conn = get_connection()
upsert_raw(conn, collect())
conn.close()
```

**Export to Excel for handoff:**

```python
from storage import get_connection
from export_excel import export_to_excel

conn = get_connection()
export_to_excel(conn)  # writes wallet_metrics.xlsx
conn.close()
```

## Testing

```bash
pytest test_collect_bitcoin.py test_collect_ethereum.py test_collect_bnb.py test_collect.py test_storage.py test_export.py -v
```

No network calls are made during tests — `requests.get` (or, for the
CSV-based adapters, `fetch_csv`) is mocked throughout.

## Output schema

Every adapter's `backfill()`/`collect()` returns the same shape, one
record per (coin, date, metric):

| Column | Type | Meaning |
|---|---|---|
| `coin` | text | `"bitcoin"`, `"ethereum"`, or `"bnb"` |
| `date` | text (YYYY-MM-DD) | the day this value applies to |
| `metric` | text | `"active_addresses"`, `"tx_count"`, or `"tx_volume"` (not all metrics exist for all coins — see the coverage table above) |
| `value` | number | the raw value for that metric that day |
| `is_partial` | bool | always `False` for this pipeline — see `design.md` |
```

- [ ] **Step 4: No git repo — skip commit. Implementation plan complete.**
