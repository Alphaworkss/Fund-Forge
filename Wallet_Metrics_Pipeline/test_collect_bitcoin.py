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


@patch("sources.bitcoin.requests.get")
def test_fetch_chart_returns_none_on_unparseable_json(mock_get):
    resp = Mock()
    resp.status_code = 200
    resp.json.side_effect = ValueError("not json")
    mock_get.return_value = resp

    values = bitcoin._fetch_chart("n-unique-addresses", "10days")

    assert values is None


@patch("sources.bitcoin.requests.get")
def test_fetch_chart_returns_none_when_values_key_missing(mock_get):
    mock_get.return_value = _fake_response(json_data={"status": "ok"})  # no "values" key

    values = bitcoin._fetch_chart("n-unique-addresses", "10days")

    assert values is None


def test_values_to_records_shape():
    records = bitcoin._values_to_records("active_addresses", SAMPLE_VALUES)

    assert records == [
        {"coin": "bitcoin", "date": "2026-07-29", "metric": "active_addresses", "value": 478468.0,
         "is_partial": False, "raw_response": {"x": 1785283200, "y": 478468.0}},
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "active_addresses", "value": 497475.0,
         "is_partial": False, "raw_response": {"x": 1785369600, "y": 497475.0}},
    ]


@patch("sources.bitcoin._fetch_chart")
def test_backfill_requests_all_three_metrics_with_all_timespan(mock_fetch):
    mock_fetch.return_value = SAMPLE_VALUES

    bitcoin.backfill()

    called_charts = {call.args[0] for call in mock_fetch.call_args_list}
    assert called_charts == {"n-unique-addresses", "n-transactions", "estimated-transaction-volume"}
    for call in mock_fetch.call_args_list:
        assert call.args[1] == "all"


@patch("sources.bitcoin._fetch_chart")
def test_backfill_returns_records_for_all_metrics(mock_fetch):
    mock_fetch.return_value = SAMPLE_VALUES

    records = bitcoin.backfill()

    assert len(records) == 6  # 2 values x 3 metrics
    assert {r["metric"] for r in records} == {"active_addresses", "tx_count", "tx_volume"}


@patch("sources.bitcoin._fetch_chart")
def test_backfill_skips_a_failed_metric_without_crashing(mock_fetch):
    def side_effect(chart, timespan):
        return None if chart == "n-transactions" else SAMPLE_VALUES

    mock_fetch.side_effect = side_effect

    records = bitcoin.backfill()

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
