"""
test_collect.py — Stage 8: Testing (collect.py's raw_response capture)

Only tests the raw_response passthrough added for the common-schema
requirement — collect()'s core keyword/date/interest extraction has no
existing unit test in this pipeline (trendspy's Trends class talks
directly to Google's live API and has no documented lightweight fake),
so this test mocks collect.Trends itself rather than the network.
"""

from unittest.mock import MagicMock, patch

import pandas as pd

import collect


def _fake_trends_df():
    idx = pd.to_datetime(["2026-07-01", "2026-07-02"])
    return pd.DataFrame({"PSX": [40, 45], "isPartial": [False, False]}, index=idx)


@patch("collect.time.sleep")
@patch("collect.Trends")
def test_collect_attaches_raw_response_per_row(mock_trends_cls, mock_sleep):
    mock_instance = MagicMock()
    mock_instance.interest_over_time.return_value = _fake_trends_df()
    mock_trends_cls.return_value = mock_instance

    records = collect.collect(keywords=["PSX"])

    assert records[0]["raw_response"] == {"PSX": 40, "isPartial": False}
    assert records[1]["raw_response"] == {"PSX": 45, "isPartial": False}
