from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from digital_oracle.providers import (
    DeribitFuturesCurveQuery,
    DeribitInstrumentsQuery,
    DeribitOptionChainQuery,
    DeribitProvider,
)


def _fixture_json(name: str) -> Any:
    path = Path(__file__).resolve().parent / "fixtures" / name
    return json.loads(path.read_text())


class FakeDeribitClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Mapping[str, object] | None]] = []
        self.futures_instruments = _fixture_json("deribit_instruments_futures.json")
        self.option_instruments = _fixture_json("deribit_instruments_options.json")
        self.futures_summaries = _fixture_json("deribit_book_summaries_futures.json")
        self.option_summaries = _fixture_json("deribit_book_summaries_options.json")
        self.order_book = _fixture_json("deribit_order_book_btc_perpetual.json")

    def get_json(self, url: str, *, params: Mapping[str, object] | None = None) -> Any:
        self.calls.append((url, params))
        if url.endswith("/get_instruments"):
            kind = params.get("kind") if params else None
            if kind == "future":
                return self.futures_instruments
            if kind == "option":
                return self.option_instruments
        if url.endswith("/get_book_summary_by_currency"):
            kind = params.get("kind") if params else None
            if kind == "future":
                return self.futures_summaries
            if kind == "option":
                return self.option_summaries
        if url.endswith("/get_order_book"):
            return self.order_book
        raise AssertionError(f"unexpected url: {url}")


class DeribitProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeDeribitClient()
        self.provider = DeribitProvider(http_client=self.fake_client)

    def test_list_instruments_parses_futures_and_sorts_by_expiry(self) -> None:
        instruments = self.provider.list_instruments(
            DeribitInstrumentsQuery(currency="BTC", kind="future")
        )

        self.assertEqual(len(instruments), 4)
        self.assertEqual(instruments[0].instrument_name, "BTC-13MAR26")
        self.assertEqual(instruments[1].instrument_name, "BTC-27MAR26")
        self.assertEqual(instruments[2].instrument_name, "BTC-26JUN26")
        self.assertEqual(instruments[3].instrument_name, "BTC-PERPETUAL")
        self.assertFalse(instruments[0].is_perpetual)
        self.assertTrue(instruments[3].is_perpetual)
        self.assertEqual(instruments[0].settlement_period, "week")
        self.assertEqual(instruments[3].tick_size, 0.5)

        _, params = self.fake_client.calls[-1]
        assert params is not None
        self.assertEqual(params["currency"], "BTC")
        self.assertEqual(params["kind"], "future")
        self.assertEqual(params["expired"], False)

    def test_get_order_book_normalizes_top_of_book_and_levels(self) -> None:
        book = self.provider.get_order_book("BTC-PERPETUAL", depth=5)

        self.assertEqual(book.instrument_name, "BTC-PERPETUAL")
        self.assertEqual(book.timestamp_ms, 1773201784300)
        self.assertAlmostEqual(book.best_bid or 0.0, 69596.0)
        self.assertAlmostEqual(book.best_ask or 0.0, 69596.5)
        self.assertAlmostEqual(book.spread or 0.0, 0.5)
        self.assertEqual(len(book.bids), 5)
        self.assertEqual(len(book.asks), 5)
        self.assertAlmostEqual(book.mark_price or 0.0, 69598.29)
        self.assertAlmostEqual(book.index_price or 0.0, 69592.32)

        _, params = self.fake_client.calls[-1]
        assert params is not None
        self.assertEqual(params["instrument_name"], "BTC-PERPETUAL")
        self.assertEqual(params["depth"], 5)

    def test_get_futures_term_structure_joins_snapshots_and_computes_basis(self) -> None:
        curve = self.provider.get_futures_term_structure(DeribitFuturesCurveQuery(currency="BTC"))

        self.assertEqual(curve.currency, "BTC")
        self.assertEqual(len(curve.points), 4)
        self.assertEqual(curve.points[0].instrument_name, "BTC-PERPETUAL")
        self.assertTrue(curve.points[0].is_perpetual)
        self.assertAlmostEqual(curve.points[0].basis_vs_perpetual or 0.0, 0.0)
        self.assertEqual(curve.points[1].instrument_name, "BTC-13MAR26")
        self.assertLess(curve.points[1].basis_vs_perpetual or 0.0, 0.0)
        self.assertEqual(curve.points[-1].instrument_name, "BTC-26JUN26")
        self.assertAlmostEqual(curve.points[-1].basis_vs_perpetual or 0.0, 0.007601, places=6)
        self.assertAlmostEqual(curve.points[-1].annualized_basis_vs_perpetual or 0.0, 0.02589, places=6)

        _, params = self.fake_client.calls[-1]
        assert params is not None
        self.assertEqual(params["currency"], "BTC")
        self.assertEqual(params["kind"], "future")

    def test_get_option_chain_groups_calls_and_puts_by_strike(self) -> None:
        chain = self.provider.get_option_chain(DeribitOptionChainQuery(currency="BTC"))

        self.assertIsNotNone(chain)
        assert chain is not None
        self.assertEqual(chain.currency, "BTC")
        self.assertEqual(chain.expiration_label, "11MAR26")
        self.assertEqual(len(chain.strikes), 3)
        self.assertEqual(chain.strikes[0].strike, 60000.0)
        self.assertEqual(chain.strikes[0].call.instrument_name if chain.strikes[0].call else None, "BTC-11MAR26-60000-C")
        self.assertEqual(chain.strikes[0].put.instrument_name if chain.strikes[0].put else None, "BTC-11MAR26-60000-P")
        self.assertAlmostEqual(chain.strikes[1].call.ask_price if chain.strikes[1].call else 0.0, 0.1275)
        self.assertIsNone(chain.strikes[1].put.bid_price if chain.strikes[1].put else None)
        self.assertEqual(chain.atm_strike().strike if chain.atm_strike() else None, 62000.0)
        self.assertEqual(chain.underlying_index, "SYN.BTC-11MAR26")

        _, params = self.fake_client.calls[-1]
        assert params is not None
        self.assertEqual(params["currency"], "BTC")
        self.assertEqual(params["kind"], "option")


if __name__ == "__main__":
    unittest.main()
