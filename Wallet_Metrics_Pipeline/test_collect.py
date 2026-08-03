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


def test_collect_returns_empty_list_when_every_adapter_returns_no_records():
    fake_adapters = {
        "bitcoin": _fake_adapter([]),
        "ethereum": _fake_adapter([]),
        "bnb": _fake_adapter([]),
    }

    with patch.dict(collect.ADAPTERS, fake_adapters, clear=True):
        records = collect.collect()

    assert records == []


def test_collect_returns_empty_list_when_every_adapter_raises():
    failing_adapters = {}
    for coin in ("bitcoin", "ethereum", "bnb"):
        adapter = MagicMock()
        adapter.collect.side_effect = RuntimeError("boom")
        failing_adapters[coin] = adapter

    with patch.dict(collect.ADAPTERS, failing_adapters, clear=True):
        records = collect.collect()

    assert records == []


def test_adapters_dict_has_exactly_the_three_in_scope_coins():
    assert set(collect.ADAPTERS.keys()) == {"bitcoin", "ethereum", "bnb"}
