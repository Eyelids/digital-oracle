from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from digital_oracle.providers.cftc import CftcCotProvider, CftcCotQuery, CftcCotReport

# ---------------------------------------------------------------------------
# Sample fixture data mimicking the CFTC SODA API response
# ---------------------------------------------------------------------------

SAMPLE_GOLD_RECORDS: list[dict[str, Any]] = [
    {
        "market_and_exchange_names": "GOLD - COMMODITY EXCHANGE INC.",
        "report_date_as_yyyy_mm_dd": "2026-03-04T00:00:00.000",
        "commodity_name": "GOLD",
        "open_interest_all": "550000",
        "prod_merc_positions_long_all": "80000",
        "prod_merc_positions_short_all": "195000",
        "swap_positions_long_all": "60000",
        "swap__positions_short_all": "72000",
        "swap__positions_spread_all": "35000",
        "m_money_positions_long_all": "180000",
        "m_money_positions_short_all": "45000",
        "m_money_positions_spread_all": "28000",
        "other_rept_positions_long_all": "52000",
        "other_rept_positions_short_all": "41000",
        "other_rept_positions_spread_all": "15000",
    },
    {
        "market_and_exchange_names": "GOLD - COMMODITY EXCHANGE INC.",
        "report_date_as_yyyy_mm_dd": "2026-02-25T00:00:00.000",
        "commodity_name": "GOLD",
        "open_interest_all": "540000",
        "prod_merc_positions_long_all": "78000",
        "prod_merc_positions_short_all": "190000",
        "swap_positions_long_all": "58000",
        "swap__positions_short_all": "70000",
        "swap__positions_spread_all": "33000",
        "m_money_positions_long_all": "175000",
        "m_money_positions_short_all": "48000",
        "m_money_positions_spread_all": "26000",
        "other_rept_positions_long_all": "50000",
        "other_rept_positions_short_all": "40000",
        "other_rept_positions_spread_all": "14000",
    },
]

SAMPLE_CRUDE_RECORDS: list[dict[str, Any]] = [
    {
        "market_and_exchange_names": "CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE",
        "report_date_as_yyyy_mm_dd": "2026-03-04T00:00:00.000",
        "commodity_name": "CRUDE OIL, LIGHT SWEET",
        "open_interest_all": "1800000",
        "prod_merc_positions_long_all": "350000",
        "prod_merc_positions_short_all": "520000",
        "swap_positions_long_all": "250000",
        "swap__positions_short_all": "310000",
        "swap__positions_spread_all": "120000",
        "m_money_positions_long_all": "420000",
        "m_money_positions_short_all": "110000",
        "m_money_positions_spread_all": "90000",
        "other_rept_positions_long_all": "100000",
        "other_rept_positions_short_all": "85000",
        "other_rept_positions_spread_all": "40000",
    },
]


class FakeJsonClient:
    """Fake HTTP client that returns sample CFTC JSON data."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Mapping[str, object] | None]] = []

    def get_json(self, url: str, *, params: Mapping[str, object] | None = None) -> Any:
        self.calls.append((url, params))
        where_clause = params.get("$where", "") if params else ""
        if isinstance(where_clause, str) and "GOLD" in where_clause:
            return list(SAMPLE_GOLD_RECORDS)
        if isinstance(where_clause, str) and "CRUDE" in where_clause:
            return list(SAMPLE_CRUDE_RECORDS)
        # No filter: return all
        return list(SAMPLE_GOLD_RECORDS) + list(SAMPLE_CRUDE_RECORDS)


class CftcCotProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeJsonClient()
        self.provider = CftcCotProvider(http_client=self.fake_client)

    # ------------------------------------------------------------------
    # Parsing tests
    # ------------------------------------------------------------------

    def test_parse_report_fields(self) -> None:
        reports = self.provider.list_reports(CftcCotQuery(commodity_name="GOLD", limit=10))

        self.assertEqual(len(reports), 2)
        r = reports[0]
        self.assertIsInstance(r, CftcCotReport)
        self.assertEqual(r.market_name, "GOLD - COMMODITY EXCHANGE INC.")
        self.assertEqual(r.report_date, "2026-03-04")
        self.assertEqual(r.commodity, "GOLD")
        self.assertEqual(r.open_interest, 550000)
        self.assertEqual(r.prod_long, 80000)
        self.assertEqual(r.prod_short, 195000)
        self.assertEqual(r.swap_long, 60000)
        self.assertEqual(r.swap_short, 72000)
        self.assertEqual(r.swap_spread, 35000)
        self.assertEqual(r.mm_long, 180000)
        self.assertEqual(r.mm_short, 45000)
        self.assertEqual(r.mm_spread, 28000)
        self.assertEqual(r.other_long, 52000)
        self.assertEqual(r.other_short, 41000)
        self.assertEqual(r.other_spread, 15000)

    def test_report_date_strips_timestamp(self) -> None:
        reports = self.provider.list_reports(CftcCotQuery(commodity_name="GOLD"))
        self.assertEqual(reports[0].report_date, "2026-03-04")
        self.assertEqual(reports[1].report_date, "2026-02-25")

    # ------------------------------------------------------------------
    # Computed property tests
    # ------------------------------------------------------------------

    def test_mm_net_property(self) -> None:
        reports = self.provider.list_reports(CftcCotQuery(commodity_name="GOLD"))
        r = reports[0]
        # mm_net = mm_long - mm_short = 180000 - 45000 = 135000
        self.assertEqual(r.mm_net, 135000)

    def test_prod_net_property(self) -> None:
        reports = self.provider.list_reports(CftcCotQuery(commodity_name="GOLD"))
        r = reports[0]
        # prod_net = prod_long - prod_short = 80000 - 195000 = -115000
        self.assertEqual(r.prod_net, -115000)

    def test_mm_net_crude(self) -> None:
        reports = self.provider.list_reports(CftcCotQuery(commodity_name="CRUDE"))
        r = reports[0]
        # mm_net = 420000 - 110000 = 310000
        self.assertEqual(r.mm_net, 310000)

    def test_prod_net_crude(self) -> None:
        reports = self.provider.list_reports(CftcCotQuery(commodity_name="CRUDE"))
        r = reports[0]
        # prod_net = 350000 - 520000 = -170000
        self.assertEqual(r.prod_net, -170000)

    # ------------------------------------------------------------------
    # Query parameter tests
    # ------------------------------------------------------------------

    def test_query_passes_commodity_filter(self) -> None:
        self.provider.list_reports(CftcCotQuery(commodity_name="gold"))
        _, params = self.fake_client.calls[-1]
        assert params is not None
        self.assertIn("$where", params)
        self.assertIn("GOLD", str(params["$where"]))

    def test_query_passes_limit(self) -> None:
        self.provider.list_reports(CftcCotQuery(commodity_name="GOLD", limit=5))
        _, params = self.fake_client.calls[-1]
        assert params is not None
        self.assertEqual(params["$limit"], 5)

    def test_query_passes_order_desc(self) -> None:
        self.provider.list_reports(CftcCotQuery(commodity_name="GOLD"))
        _, params = self.fake_client.calls[-1]
        assert params is not None
        self.assertEqual(params["$order"], "report_date_as_yyyy_mm_dd DESC")

    def test_query_without_commodity_name_omits_where(self) -> None:
        self.provider.list_reports(CftcCotQuery())
        _, params = self.fake_client.calls[-1]
        assert params is not None
        self.assertNotIn("$where", params)

    def test_default_query_when_none(self) -> None:
        reports = self.provider.list_reports(CftcCotQuery(primary_only=False))
        # No filter returns all records from the fake
        self.assertEqual(len(reports), 3)

    def test_primary_only_deduplicates_by_date(self) -> None:
        reports = self.provider.list_reports(CftcCotQuery(primary_only=True))
        # 2026-03-04 has both GOLD (OI=550K) and CRUDE (OI=1.8M);
        # primary_only keeps only CRUDE (higher OI) for that date.
        self.assertEqual(len(reports), 2)
        dates = [r.report_date for r in reports]
        self.assertEqual(dates, ["2026-03-04", "2026-02-25"])
        # The 2026-03-04 record should be CRUDE (highest OI)
        self.assertEqual(reports[0].commodity, "CRUDE OIL, LIGHT SWEET")
        # The 2026-02-25 record should be GOLD (only one on that date)
        self.assertEqual(reports[1].commodity, "GOLD")

    # ------------------------------------------------------------------
    # Provider metadata
    # ------------------------------------------------------------------

    def test_provider_metadata(self) -> None:
        meta = self.provider.describe()
        self.assertEqual(meta.provider_id, "cftc_cot")
        self.assertEqual(meta.display_name, "CFTC Commitments of Traders")
        self.assertIn("positioning", meta.capabilities)

    # ------------------------------------------------------------------
    # Frozen dataclass
    # ------------------------------------------------------------------

    def test_report_is_frozen(self) -> None:
        reports = self.provider.list_reports(CftcCotQuery(commodity_name="GOLD"))
        with self.assertRaises(AttributeError):
            reports[0].mm_long = 999  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_empty_response(self) -> None:
        class EmptyClient:
            def get_json(self, url: str, *, params: Mapping[str, object] | None = None) -> Any:
                return []

        provider = CftcCotProvider(http_client=EmptyClient())
        reports = provider.list_reports(CftcCotQuery(commodity_name="NONEXISTENT"))
        self.assertEqual(reports, [])

    def test_missing_fields_default_to_zero(self) -> None:
        class SparseClient:
            def get_json(self, url: str, *, params: Mapping[str, object] | None = None) -> Any:
                return [
                    {
                        "market_and_exchange_names": "TEST MARKET",
                        "report_date_as_yyyy_mm_dd": "2026-01-01T00:00:00.000",
                        "commodity_name": "TEST",
                        # All numeric fields missing
                    }
                ]

        provider = CftcCotProvider(http_client=SparseClient())
        reports = provider.list_reports()
        self.assertEqual(len(reports), 1)
        r = reports[0]
        self.assertEqual(r.commodity, "TEST")
        self.assertEqual(r.open_interest, 0)
        self.assertEqual(r.mm_long, 0)
        self.assertEqual(r.mm_short, 0)
        self.assertEqual(r.mm_net, 0)
        self.assertEqual(r.prod_net, 0)


if __name__ == "__main__":
    unittest.main()
