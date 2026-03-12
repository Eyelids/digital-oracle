from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from digital_oracle.providers import PriceHistoryQuery, StooqProvider


def _fixture_text(name: str) -> str:
    path = Path(__file__).resolve().parent / "fixtures" / name
    return path.read_text()


class FakeStooqClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Mapping[str, object] | None]] = []
        self.spy_history = _fixture_text("stooq_spy.csv")
        self.gold_history = _fixture_text("stooq_xauusd.csv")

    def get_text(self, url: str, *, params: Mapping[str, object] | None = None) -> str:
        self.calls.append((url, params))
        symbol = params.get("s") if params else None
        if symbol == "spy.us":
            return self.spy_history
        if symbol == "xauusd":
            return self.gold_history
        return "No data"


class StooqProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeStooqClient()
        self.provider = StooqProvider(http_client=self.fake_client)

    def test_get_history_parses_ohlcv_and_limit(self) -> None:
        history = self.provider.get_history(
            PriceHistoryQuery(symbol="SPY.US", interval="d", limit=2)
        )

        self.assertEqual(history.symbol, "spy.us")
        self.assertEqual(history.raw_symbol, "SPY.US")
        self.assertEqual(history.interval, "d")
        self.assertEqual(len(history.bars), 2)
        self.assertEqual(history.bars[0].date, "2026-03-06")
        self.assertAlmostEqual(history.bars[0].close, 671.43)
        self.assertAlmostEqual(history.latest.close if history.latest else 0.0, 674.72)
        self.assertEqual(history.latest.volume if history.latest else None, 114253159.0)

        _, params = self.fake_client.calls[-1]
        assert params is not None
        self.assertEqual(params["s"], "spy.us")
        self.assertEqual(params["i"], "d")

    def test_get_history_handles_missing_volume_and_date_filters(self) -> None:
        history = self.provider.get_history(
            PriceHistoryQuery(
                symbol="xauusd",
                start_date="2026-03-06",
                end_date="2026-03-09",
            )
        )

        self.assertEqual(len(history.bars), 2)
        self.assertIsNone(history.bars[0].volume)
        self.assertEqual(history.earliest.date if history.earliest else None, "2026-03-06")
        self.assertEqual(history.latest.date if history.latest else None, "2026-03-09")

    def test_get_history_returns_empty_for_no_data(self) -> None:
        history = self.provider.get_history(PriceHistoryQuery(symbol="missing.us"))
        self.assertEqual(history.bars, ())


if __name__ == "__main__":
    unittest.main()
