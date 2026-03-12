from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from digital_oracle.providers import KalshiMarketQuery, KalshiProvider


def _fixture_json(name: str) -> Any:
    path = Path(__file__).resolve().parent / "fixtures" / name
    return json.loads(path.read_text())


class FakeKalshiClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Mapping[str, object] | None]] = []
        self.markets_payload = _fixture_json("kalshi_markets.json")
        self.market_detail_payload = _fixture_json("kalshi_market_detail.json")
        self.event_payload = _fixture_json("kalshi_event.json")
        self.orderbook_payload = _fixture_json("kalshi_orderbook.json")

    def get_json(self, url: str, *, params: Mapping[str, object] | None = None) -> Any:
        self.calls.append((url, params))
        if url.endswith("/markets"):
            return self.markets_payload
        if url.endswith("/markets/KXFED-27APR-T4.25"):
            return self.market_detail_payload
        if url.endswith("/events/KXFED-27APR"):
            return self.event_payload
        if url.endswith("/markets/KXFED-27APR-T4.25/orderbook"):
            return self.orderbook_payload
        raise AssertionError(f"unexpected url: {url}")


class KalshiProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeKalshiClient()
        self.provider = KalshiProvider(http_client=self.fake_client)

    def test_list_markets_normalizes_probability_fields_and_query_params(self) -> None:
        markets = self.provider.list_markets(
            KalshiMarketQuery(limit=3, status="open", series_ticker="KXFED")
        )

        self.assertEqual(len(markets), 3)
        self.assertEqual(markets[0].ticker, "KXFED-27APR-T4.25")
        self.assertAlmostEqual(markets[0].yes_bid or 0.0, 0.02)
        self.assertAlmostEqual(markets[0].yes_ask or 0.0, 0.36)
        self.assertAlmostEqual(markets[0].no_bid or 0.0, 0.64)
        self.assertAlmostEqual(markets[0].midpoint or 0.0, 0.19)
        self.assertAlmostEqual(markets[0].floor_strike or 0.0, 4.25)

        _, params = self.fake_client.calls[-1]
        assert params is not None
        self.assertEqual(params["limit"], 3)
        self.assertEqual(params["status"], "open")
        self.assertEqual(params["series_ticker"], "KXFED")
        self.assertEqual(params["mve_filter"], "exclude")

    def test_get_market_returns_single_market_snapshot(self) -> None:
        market = self.provider.get_market("KXFED-27APR-T4.25")

        self.assertEqual(market.ticker, "KXFED-27APR-T4.25")
        self.assertEqual(market.event_ticker, "KXFED-27APR")
        self.assertAlmostEqual(market.last_price or 0.0, 0.03)
        self.assertAlmostEqual(market.yes_bid or 0.0, 0.03)
        self.assertAlmostEqual(market.yes_ask or 0.0, 0.35)
        self.assertEqual(market.status, "active")

    def test_get_event_groups_markets_and_ranks_most_active_market(self) -> None:
        event = self.provider.get_event("KXFED-27APR")

        self.assertEqual(event.event_ticker, "KXFED-27APR")
        self.assertEqual(event.series_ticker, "KXFED")
        self.assertEqual(event.category, "Economics")
        self.assertEqual(len(event.markets), 3)
        self.assertEqual(event.market_by_ticker("KXFED-27APR-T4.00").subtitle, "4.00%")
        self.assertEqual(event.most_active_market().ticker, "KXFED-27APR-T3.75")

    def test_get_orderbook_derives_asks_from_opposite_side(self) -> None:
        book = self.provider.get_order_book("KXFED-27APR-T4.25", depth=10)

        self.assertEqual(len(book.yes_bids), 2)
        self.assertEqual(len(book.no_bids), 10)
        self.assertAlmostEqual(book.best_yes_bid or 0.0, 0.03)
        self.assertAlmostEqual(book.best_no_bid or 0.0, 0.65)
        self.assertAlmostEqual(book.best_yes_ask or 0.0, 0.35)
        self.assertAlmostEqual(book.best_no_ask or 0.0, 0.97)
        self.assertAlmostEqual(book.yes_spread or 0.0, 0.32)
        self.assertAlmostEqual(book.midpoint or 0.0, 0.19)

        _, params = self.fake_client.calls[-1]
        assert params is not None
        self.assertEqual(params["depth"], 10)


if __name__ == "__main__":
    unittest.main()
