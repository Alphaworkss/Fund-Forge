"""
test_collect_bnb.py — Stage 8: Testing (sources/bnb.py)

Mocks fetch_csv so these tests never touch the network or the real
BscScan site. Run with: pytest test_collect_bnb.py
"""

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


def test_parse_tx_rows_includes_raw_response():
    rows = [{"Date(UTC)": "07/30/2026", "UnixTimeStamp": "1785369600", "Value": "300000"}]

    records = bnb._parse_tx_rows(rows)

    assert records[0]["raw_response"] == rows[0]


@patch("sources.bnb.fetch_csv")
def test_backfill_returns_full_history_no_filtering(mock_fetch_csv):
    mock_fetch_csv.return_value = [
        {"Date(UTC)": "8/29/2020", "UnixTimeStamp": "1598659200", "Value": "122"},
        {"Date(UTC)": "7/30/2026", "UnixTimeStamp": "1785369600", "Value": "16323969"},
    ]

    records = bnb.backfill()

    dates = {r["date"] for r in records}
    assert "2020-08-29" in dates
    assert "2026-07-30" in dates


@patch("sources.bnb.fetch_csv")
def test_backfill_calls_fetch_csv_with_bnb_tx_chart_url(mock_fetch_csv):
    mock_fetch_csv.return_value = TX_CSV_ROWS

    bnb.backfill()

    mock_fetch_csv.assert_called_once_with("https://bscscan.com/chart/tx?output=csv")
