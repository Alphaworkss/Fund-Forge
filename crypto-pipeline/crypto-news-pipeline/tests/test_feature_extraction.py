"""Tests for processing/feature_extraction.py with known expected outputs."""

import pytest

from processing.feature_extraction import (
    classify_event_category,
    compute_importance,
    detect_affected_coins,
    extract_features,
    score_sentiment,
)
from processing.normalization import normalize_record


class TestDetectAffectedCoins:
    def test_names_case_insensitive(self):
        assert detect_affected_coins("bitcoin and ethereum are rallying") == "BTC,ETH"

    def test_tickers_matched(self):
        assert detect_affected_coins("BTC breaks resistance while SOL lags") == "BTC,SOL"

    def test_no_coins(self):
        assert detect_affected_coins("Stock markets closed higher today") == ""

    def test_deduped(self):
        assert detect_affected_coins("Bitcoin! BTC! bitcoin again!") == "BTC"

    def test_multiword_name(self):
        assert detect_affected_coins("Shiba Inu community celebrates") == "SHIB"

    def test_ticker_not_matched_in_lowercase_word(self):
        # "dot" inside a normal lowercase sentence should not match DOT ticker
        assert "DOT" not in detect_affected_coins("connect the dots carefully")


class TestClassifyEventCategory:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Binance will list PEPE with new trading pair", "Exchange Listing"),
            ("Kraken announces delisting of XMR for EU users", "Delisting"),
            ("BNB quarterly token burn completed", "Token Burn"),
            ("Ethereum devs schedule hard fork for March", "Fork"),
            ("Claim your airdrop of ARB tokens now", "Airdrop"),
            ("Spot Bitcoin ETF sees record inflow", "ETF News"),
            ("Users report wallet drained via smart contract exploit", "Wallet Exploit"),
            ("Exchange hacked: hot wallet compromised overnight", "Exchange Hack"),
            ("Network congestion drives high gas fees on Ethereum", "Network Congestion"),
            ("Scheduled wallet maintenance this weekend", "Maintenance Notice"),
            ("Trading halted amid platform outage", "Exchange Outage"),
            ("SEC files lawsuit against crypto firm", "Regulatory Announcement"),
            ("Cats are cute and dogs are loyal", "Other"),
        ],
    )
    def test_categories(self, text, expected):
        assert classify_event_category(text) == expected


class TestScoreSentiment:
    def test_positive(self):
        assert score_sentiment("This is fantastic great wonderful news!") > 0.5

    def test_negative(self):
        assert score_sentiment("Terrible disastrous hack, users devastated") < -0.5

    def test_neutral_empty(self):
        assert score_sentiment("") == 0.0

    def test_range(self):
        for text in ["amazing!!!", "horrible!!!", "the sky is blue"]:
            assert -1.0 <= score_sentiment(text) <= 1.0


class TestComputeImportance:
    def test_base_only(self):
        assert compute_importance("Other", "news", 0.0) == pytest.approx(0.3)

    def test_high_category(self):
        assert compute_importance("Exchange Hack", "news", 0.0) == pytest.approx(0.6)

    def test_medium_category(self):
        assert compute_importance("ETF News", "news", 0.0) == pytest.approx(0.5)

    def test_official_source_bonus(self):
        assert compute_importance("Other", "exchange_announcement", 0.0) == pytest.approx(0.4)

    def test_strong_sentiment_bonus(self):
        assert compute_importance("Other", "news", 0.8) == pytest.approx(0.4)
        assert compute_importance("Other", "news", -0.8) == pytest.approx(0.4)

    def test_sentiment_at_threshold_no_bonus(self):
        assert compute_importance("Other", "news", 0.5) == pytest.approx(0.3)

    def test_max_stack_clamped(self):
        # 0.3 + 0.3 + 0.1 + 0.1 = 0.8 (no clamp needed but verify)
        assert compute_importance("Exchange Hack", "exchange_announcement", 0.9) == pytest.approx(0.8)

    def test_clamped_to_valid_range(self):
        score = compute_importance("Exchange Hack", "exchange_announcement", 1.0)
        assert 0.0 <= score <= 1.0


class TestExtractFeatures:
    def test_full_extraction_known_output(self):
        record = normalize_record(
            {
                "title": "Binance will list Solana perpetuals",
                "url": "https://binance.com/announce/42",
                "published_at": "2025-01-06T14:30:00+00:00",
                "raw_content": "Binance announces a new SOL trading pair launching Friday.",
                "source_name": "Binance",
                "source_type": "exchange_announcement",
            }
        )
        result = extract_features(record)
        assert result["event_category"] == "Exchange Listing"
        assert "SOL" in result["affected_coins"]
        # base 0.3 + listing 0.2 + official 0.1 (+ maybe sentiment bonus)
        assert result["importance_score"] >= 0.6
        assert -1.0 <= result["sentiment_score"] <= 1.0

    def test_original_record_not_mutated(self):
        record = normalize_record(
            {
                "title": "Bitcoin ETF approved",
                "url": "https://a.com/1",
                "published_at": "2025-01-06T14:30:00+00:00",
                "raw_content": "Great news for bitcoin holders.",
                "source_name": "CoinDesk",
                "source_type": "news",
            }
        )
        extract_features(record)
        assert record["event_category"] == "Other"  # untouched
