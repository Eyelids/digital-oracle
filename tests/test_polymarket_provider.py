from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from digital_oracle.providers import PolymarketEventQuery, PolymarketProvider


def _fixture(name: str) -> Any:
    path = Path(__file__).resolve().parent / "fixtures" / name
    return json.loads(path.read_text())


class FakeJsonClient:
    def __init__(self, *, events_payload: list[Mapping[str, Any]], book_payload: Mapping[str, Any]):
        self.events_payload = events_payload
        self.book_payload = book_payload
        self.calls: list[tuple[str, Mapping[str, object] | None]] = []

    def get_json(self, url: str, *, params: Mapping[str, object] | None = None) -> Any:
        self.calls.append((url, params))
        if url.endswith("/events"):
            if params and params.get("slug") == "missing-slug":
                return []
            return self.events_payload
        if url.endswith("/book"):
            return self.book_payload
        raise AssertionError(f"unexpected url: {url}")


class PolymarketProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeJsonClient(
            events_payload=_fixture("polymarket_events.json"),
            book_payload=_fixture("polymarket_book.json"),
        )
        self.provider = PolymarketProvider(http_client=self.fake_client)

    def test_list_events_normalizes_primary_market_and_probabilities(self) -> None:
        events = self.provider.list_events(PolymarketEventQuery(limit=1))
        self.assertEqual(len(events), 1)

        event = events[0]
        market = event.primary_market()

        self.assertIsNotNone(market)
        assert market is not None
        self.assertEqual(event.slug, "microstrategy-sell-any-bitcoin-in-2025")
        self.assertEqual(market.slug, "microstrategy-sells-any-bitcoin-by-december-31-2026")
        self.assertAlmostEqual(market.yes_probability or 0.0, 0.155)
        self.assertEqual(
            market.token_id_for("yes"),
            "111128191581505463501777127559667396812474366956707382672202929745167742497287",
        )
        self.assertEqual(self.fake_client.calls[0][1]["order"], "volume24hr")

    def test_get_event_returns_none_when_missing(self) -> None:
        event = self.provider.get_event("missing-slug")
        self.assertIsNone(event)

    def test_get_order_book_sorts_levels_and_computes_spread(self) -> None:
        book = self.provider.get_order_book(
            "111128191581505463501777127559667396812474366956707382672202929745167742497287"
        )

        self.assertEqual(book.timestamp_ms, 1773198857001)
        self.assertAlmostEqual(book.best_bid or 0.0, 0.15)
        self.assertAlmostEqual(book.best_ask or 0.0, 0.16)
        self.assertAlmostEqual(book.spread or 0.0, 0.01)
        self.assertEqual(len(book.bids), 3)
        self.assertEqual(len(book.asks), 3)


if __name__ == "__main__":
    unittest.main()
