from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from digital_oracle.providers import ExchangeRateQuery, USTreasuryProvider, YieldCurveQuery


def _fixture_text(name: str) -> str:
    path = Path(__file__).resolve().parent / "fixtures" / name
    return path.read_text()


def _fixture_json(name: str) -> Any:
    return json.loads(_fixture_text(name))


class FakeTreasuryClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Mapping[str, object] | None]] = []
        self.nominal_curve = _fixture_text("treasury_nominal_curve.csv")
        self.real_curve = _fixture_text("treasury_real_curve.csv")
        self.exchange_rates = _fixture_json("treasury_exchange_rates.json")

    def get_text(self, url: str, *, params: Mapping[str, object] | None = None) -> str:
        self.calls.append(("text", url, params))
        curve_type = params.get("type") if params else None
        if curve_type == "daily_treasury_yield_curve":
            return self.nominal_curve
        if curve_type == "daily_treasury_real_yield_curve":
            return self.real_curve
        raise AssertionError(f"unexpected curve type: {curve_type}")

    def get_json(self, url: str, *, params: Mapping[str, object] | None = None) -> Any:
        self.calls.append(("json", url, params))
        if url.endswith("/rates_of_exchange"):
            return self.exchange_rates
        raise AssertionError(f"unexpected url: {url}")


class USTreasuryProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeTreasuryClient()
        self.provider = USTreasuryProvider(http_client=self.fake_client)

    def test_latest_nominal_yield_curve_supports_spreads(self) -> None:
        latest = self.provider.latest_yield_curve(YieldCurveQuery(year=2026, curve_kind="nominal"))

        self.assertIsNotNone(latest)
        assert latest is not None
        self.assertEqual(latest.date, "03/10/2026")
        self.assertAlmostEqual(latest.yield_for("10Y") or 0.0, 4.15)
        self.assertAlmostEqual(latest.yield_for("2 yr") or 0.0, 3.57)
        self.assertAlmostEqual(latest.spread("10Y", "2Y") or 0.0, 0.58)
        self.assertAlmostEqual(latest.spread("30Y", "10Y") or 0.0, 0.63)

    def test_real_curve_normalizes_uppercase_tenors(self) -> None:
        latest = self.provider.latest_yield_curve(YieldCurveQuery(year=2026, curve_kind="real"))

        self.assertIsNotNone(latest)
        assert latest is not None
        self.assertEqual(latest.date, "03/10/2026")
        self.assertAlmostEqual(latest.yield_for("10 yr") or 0.0, 1.82)
        self.assertAlmostEqual(latest.yield_for("30Y") or 0.0, 2.56)

    def test_exchange_rates_build_filter_and_parse_records(self) -> None:
        records = self.provider.list_exchange_rates(
            ExchangeRateQuery(
                countries=("Japan", "China"),
                record_date_gte="2024-01-01",
                limit=10,
            )
        )

        self.assertEqual(len(records), 3)
        self.assertEqual(records[0].country, "Japan")
        self.assertEqual(records[0].country_currency_desc, "Japan-Yen")
        self.assertEqual(records[1].currency, "Renminbi")
        self.assertAlmostEqual(records[1].exchange_rate or 0.0, 6.998)

        call_kind, _, params = self.fake_client.calls[-1]
        self.assertEqual(call_kind, "json")
        assert params is not None
        self.assertEqual(params["page[size]"], 10)
        self.assertEqual(
            params["fields"],
            "record_date,country,currency,country_currency_desc,exchange_rate",
        )
        self.assertEqual(
            params["filter"],
            "country:in:(Japan,China),record_date:gte:2024-01-01",
        )


if __name__ == "__main__":
    unittest.main()
