from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from digital_oracle.providers.coingecko import (
    COINGECKO_BASE,
    CoinGeckoMarketQuery,
    CoinGeckoPriceQuery,
    CoinGeckoProvider,
)


# ---------------------------------------------------------------------------
# Sample payloads mirroring CoinGecko's free API
# ---------------------------------------------------------------------------

SIMPLE_PRICE_PAYLOAD: dict[str, Any] = {
    "bitcoin": {
        "usd": 69520.0,
        "usd_market_cap": 1390360296376.65,
        "usd_24h_vol": 50877311856.89,
        "usd_24h_change": -1.23,
    },
    "ethereum": {
        "usd": 3480.12,
        "usd_market_cap": 418000000000.0,
        "usd_24h_vol": 18500000000.0,
        "usd_24h_change": 2.45,
    },
}

GLOBAL_PAYLOAD: dict[str, Any] = {
    "data": {
        "active_cryptocurrencies": 14832,
        "total_market_cap": {"usd": 2450000000000.0, "eur": 2300000000000.0},
        "total_volume": {"usd": 98000000000.0, "eur": 92000000000.0},
        "market_cap_percentage": {"btc": 56.9, "eth": 9.93},
        "market_cap_change_percentage_24h_usd": -0.85,
    }
}

MARKETS_PAYLOAD: list[dict[str, Any]] = [
    {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "current_price": 69520.0,
        "market_cap": 1390360296376,
        "market_cap_rank": 1,
        "total_volume": 50877311856,
        "price_change_percentage_24h": -1.23,
        "high_24h": 70800.0,
        "low_24h": 68200.0,
        "ath": 73738.0,
        "atl": 67.81,
    },
    {
        "id": "ethereum",
        "symbol": "eth",
        "name": "Ethereum",
        "current_price": 3480.12,
        "market_cap": 418000000000,
        "market_cap_rank": 2,
        "total_volume": 18500000000,
        "price_change_percentage_24h": 2.45,
        "high_24h": 3520.0,
        "low_24h": 3390.0,
        "ath": 4878.26,
        "atl": 0.432979,
    },
    {
        "id": "solana",
        "symbol": "sol",
        "name": "Solana",
        "current_price": 145.30,
        "market_cap": 66700000000,
        "market_cap_rank": 5,
        "total_volume": 3200000000,
        "price_change_percentage_24h": -3.10,
        "high_24h": 152.0,
        "low_24h": 140.0,
        "ath": 260.06,
        "atl": 0.50052,
    },
]


# ---------------------------------------------------------------------------
# Fake HTTP client
# ---------------------------------------------------------------------------


class FakeJsonClient:
    def __init__(
        self,
        *,
        price_payload: dict[str, Any] = SIMPLE_PRICE_PAYLOAD,
        global_payload: dict[str, Any] = GLOBAL_PAYLOAD,
        markets_payload: list[dict[str, Any]] = MARKETS_PAYLOAD,
    ):
        self.price_payload = price_payload
        self.global_payload = global_payload
        self.markets_payload = markets_payload
        self.calls: list[tuple[str, Mapping[str, object] | None]] = []

    def get_json(self, url: str, *, params: Mapping[str, object] | None = None) -> Any:
        self.calls.append((url, params))
        if "/simple/price" in url:
            return self.price_payload
        if url.endswith("/global"):
            return self.global_payload
        if "/coins/markets" in url:
            return self.markets_payload
        raise AssertionError(f"unexpected url: {url}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class CoinGeckoProviderDescribeTests(unittest.TestCase):
    def test_describe_metadata(self) -> None:
        provider = CoinGeckoProvider(http_client=FakeJsonClient())
        meta = provider.describe()
        self.assertEqual(meta.provider_id, "coingecko")
        self.assertEqual(meta.display_name, "CoinGecko")
        self.assertIn("crypto_prices", meta.capabilities)
        self.assertIn("crypto_global", meta.capabilities)


class CoinGeckoPriceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeJsonClient()
        self.provider = CoinGeckoProvider(http_client=self.fake_client)

    def test_get_prices_default_query(self) -> None:
        prices = self.provider.get_prices()
        self.assertEqual(len(prices), 2)

        btc = prices[0]
        self.assertEqual(btc.coin_id, "bitcoin")
        self.assertAlmostEqual(btc.price_usd, 69520.0)
        self.assertAlmostEqual(btc.market_cap_usd or 0, 1390360296376.65)
        self.assertAlmostEqual(btc.volume_24h_usd or 0, 50877311856.89)
        self.assertAlmostEqual(btc.price_change_24h_pct or 0, -1.23)

        eth = prices[1]
        self.assertEqual(eth.coin_id, "ethereum")
        self.assertAlmostEqual(eth.price_usd, 3480.12)

    def test_get_prices_custom_query(self) -> None:
        query = CoinGeckoPriceQuery(
            coin_ids=("bitcoin",),
            include_market_cap=False,
            include_24h_vol=False,
        )
        prices = self.provider.get_prices(query)
        self.assertEqual(len(prices), 1)
        self.assertEqual(prices[0].coin_id, "bitcoin")

        # Verify the HTTP params sent
        url, params = self.fake_client.calls[0]
        self.assertIn("/simple/price", url)
        self.assertEqual(params["ids"], "bitcoin")
        self.assertEqual(params["include_market_cap"], False)
        self.assertEqual(params["include_24hr_vol"], False)

    def test_get_prices_skips_missing_coins(self) -> None:
        query = CoinGeckoPriceQuery(coin_ids=("bitcoin", "nonexistent"))
        prices = self.provider.get_prices(query)
        self.assertEqual(len(prices), 1)
        self.assertEqual(prices[0].coin_id, "bitcoin")

    def test_get_prices_sends_correct_url(self) -> None:
        self.provider.get_prices()
        url, _ = self.fake_client.calls[0]
        self.assertEqual(url, f"{COINGECKO_BASE}/simple/price")


class CoinGeckoGlobalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeJsonClient()
        self.provider = CoinGeckoProvider(http_client=self.fake_client)

    def test_get_global_parses_all_fields(self) -> None:
        data = self.provider.get_global()
        self.assertAlmostEqual(data.total_market_cap_usd, 2450000000000.0)
        self.assertAlmostEqual(data.total_volume_24h_usd, 98000000000.0)
        self.assertAlmostEqual(data.btc_dominance_pct, 56.9)
        self.assertAlmostEqual(data.eth_dominance_pct, 9.93)
        self.assertAlmostEqual(data.market_cap_change_24h_pct, -0.85)
        self.assertEqual(data.active_cryptocurrencies, 14832)

    def test_get_global_sends_correct_url(self) -> None:
        self.provider.get_global()
        url, _ = self.fake_client.calls[0]
        self.assertEqual(url, f"{COINGECKO_BASE}/global")

    def test_get_global_rejects_bad_payload(self) -> None:
        bad_client = FakeJsonClient(global_payload={"data": "not-a-dict"})
        provider = CoinGeckoProvider(http_client=bad_client)
        with self.assertRaises(Exception):
            provider.get_global()


class CoinGeckoMarketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeJsonClient()
        self.provider = CoinGeckoProvider(http_client=self.fake_client)

    def test_list_markets_default_query(self) -> None:
        markets = self.provider.list_markets()
        self.assertEqual(len(markets), 3)

        btc = markets[0]
        self.assertEqual(btc.coin_id, "bitcoin")
        self.assertEqual(btc.symbol, "btc")
        self.assertEqual(btc.name, "Bitcoin")
        self.assertAlmostEqual(btc.current_price, 69520.0)
        self.assertAlmostEqual(btc.market_cap, 1390360296376.0)
        self.assertEqual(btc.market_cap_rank, 1)
        self.assertAlmostEqual(btc.total_volume, 50877311856.0)
        self.assertAlmostEqual(btc.price_change_24h_pct or 0, -1.23)
        self.assertAlmostEqual(btc.high_24h or 0, 70800.0)
        self.assertAlmostEqual(btc.low_24h or 0, 68200.0)
        self.assertAlmostEqual(btc.ath or 0, 73738.0)
        self.assertAlmostEqual(btc.atl or 0, 67.81)

    def test_list_markets_custom_pagination(self) -> None:
        query = CoinGeckoMarketQuery(per_page=10, page=2, order="volume_desc")
        self.provider.list_markets(query)

        url, params = self.fake_client.calls[0]
        self.assertIn("/coins/markets", url)
        self.assertEqual(params["per_page"], 10)
        self.assertEqual(params["page"], 2)
        self.assertEqual(params["order"], "volume_desc")
        self.assertEqual(params["vs_currency"], "usd")

    def test_list_markets_solana_fields(self) -> None:
        markets = self.provider.list_markets()
        sol = markets[2]
        self.assertEqual(sol.coin_id, "solana")
        self.assertEqual(sol.symbol, "sol")
        self.assertEqual(sol.market_cap_rank, 5)
        self.assertAlmostEqual(sol.current_price, 145.30)

    def test_list_markets_sends_correct_url(self) -> None:
        self.provider.list_markets()
        url, _ = self.fake_client.calls[0]
        self.assertEqual(url, f"{COINGECKO_BASE}/coins/markets")


if __name__ == "__main__":
    unittest.main()
