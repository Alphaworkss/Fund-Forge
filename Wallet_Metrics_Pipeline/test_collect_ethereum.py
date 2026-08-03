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
def test_collect_skips_tx_count_when_its_csv_has_a_renamed_column(mock_fetch_csv):
    bad_tx_csv = (
        '"Date(UTC)","UnixTimeStamp","RenamedValueColumn"\r\n'
        '"7/30/2026","1785369600","1766208"\r\n'
    )

    def side_effect(url):
        if "active-address" in url:
            return list(__import__("csv").DictReader(ACTIVE_ADDRESS_CSV.splitlines()))
        return list(__import__("csv").DictReader(bad_tx_csv.splitlines()))

    mock_fetch_csv.side_effect = side_effect

    records = ethereum.collect()

    assert {r["metric"] for r in records} == {"active_addresses"}


def test_parse_tx_rows_includes_raw_response():
    rows = [{"Date(UTC)": "07/30/2026", "UnixTimeStamp": "1785369600", "Value": "1200000"}]

    records = ethereum._parse_tx_rows(rows)

    assert records[0]["raw_response"] == rows[0]


def test_parse_active_address_rows_includes_raw_response():
    rows = [{"Date(UTC)": "07/30/2026", "UnixTimeStamp": "1785369600", "Unique Address Total Count": "500000"}]

    records = ethereum._parse_active_address_rows(rows)

    assert records[0]["raw_response"] == rows[0]


@patch("sources.ethereum.fetch_csv")
def test_backfill_returns_full_history_no_filtering(mock_fetch_csv):
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

    records = ethereum.backfill()

    dates = {r["date"] for r in records}
    assert "2015-01-01" in dates
    assert "2026-07-30" in dates
