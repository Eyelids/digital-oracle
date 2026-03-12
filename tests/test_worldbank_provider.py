from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from digital_oracle.providers.worldbank import (
    WorldBankProvider,
    WorldBankQuery,
)

SAMPLE_GDP_RESPONSE: list[Any] = [
    {
        "page": 1,
        "pages": 1,
        "per_page": 500,
        "total": 4,
    },
    [
        {
            "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
            "country": {"id": "US", "value": "United States"},
            "countryiso3code": "USA",
            "date": "2024",
            "value": 28781083.926,
            "unit": "",
            "obs_status": "",
            "decimal": 0,
        },
        {
            "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
            "country": {"id": "US", "value": "United States"},
            "countryiso3code": "USA",
            "date": "2023",
            "value": 27360935.0,
            "unit": "",
            "obs_status": "",
            "decimal": 0,
        },
        {
            "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
            "country": {"id": "CN", "value": "China"},
            "countryiso3code": "CHN",
            "date": "2024",
            "value": 18532633.0,
            "unit": "",
            "obs_status": "",
            "decimal": 0,
        },
        {
            "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
            "country": {"id": "CN", "value": "China"},
            "countryiso3code": "CHN",
            "date": "2023",
            "value": 17794782.0,
            "unit": "",
            "obs_status": "",
            "decimal": 0,
        },
    ],
]

SAMPLE_WITH_NULLS_RESPONSE: list[Any] = [
    {"page": 1, "pages": 1, "per_page": 500, "total": 3},
    [
        {
            "indicator": {"id": "SL.UEM.TOTL.ZS", "value": "Unemployment (% of labor force)"},
            "country": {"id": "US", "value": "United States"},
            "countryiso3code": "USA",
            "date": "2025",
            "value": None,
            "unit": "",
            "obs_status": "",
            "decimal": 1,
        },
        {
            "indicator": {"id": "SL.UEM.TOTL.ZS", "value": "Unemployment (% of labor force)"},
            "country": {"id": "US", "value": "United States"},
            "countryiso3code": "USA",
            "date": "2024",
            "value": 4.1,
            "unit": "",
            "obs_status": "",
            "decimal": 1,
        },
        {
            "indicator": {"id": "SL.UEM.TOTL.ZS", "value": "Unemployment (% of labor force)"},
            "country": {"id": "US", "value": "United States"},
            "countryiso3code": "USA",
            "date": "2023",
            "value": 3.6,
            "unit": "",
            "obs_status": "",
            "decimal": 1,
        },
    ],
]

SAMPLE_EMPTY_DATA_RESPONSE: list[Any] = [
    {"page": 0, "pages": 0, "per_page": 500, "total": 0},
    None,
]


class FakeJsonClient:
    def __init__(self, response: Any = None) -> None:
        self.response = response
        self.calls: list[tuple[str, Mapping[str, object] | None]] = []

    def get_json(self, url: str, *, params: Mapping[str, object] | None = None) -> Any:
        self.calls.append((url, params))
        return self.response


class WorldBankProviderIndicatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeJsonClient(SAMPLE_GDP_RESPONSE)
        self.provider = WorldBankProvider(http_client=self.fake_client)

    def test_parse_indicator_data(self) -> None:
        result = self.provider.get_indicator(
            WorldBankQuery(indicator="NY.GDP.MKTP.CD", countries=("US", "CN"))
        )

        self.assertEqual(result.indicator_id, "NY.GDP.MKTP.CD")
        self.assertEqual(result.indicator_name, "GDP (current US$)")
        self.assertEqual(len(result.points), 4)

    def test_first_point_is_correct(self) -> None:
        result = self.provider.get_indicator(
            WorldBankQuery(indicator="NY.GDP.MKTP.CD", countries=("US", "CN"))
        )

        first = result.points[0]
        self.assertEqual(first.country_code, "US")
        self.assertEqual(first.country_name, "United States")
        self.assertEqual(first.indicator_id, "NY.GDP.MKTP.CD")
        self.assertEqual(first.date, "2024")
        self.assertAlmostEqual(first.value or 0.0, 28781083.926)

    def test_multiple_countries_parsed(self) -> None:
        result = self.provider.get_indicator(
            WorldBankQuery(indicator="NY.GDP.MKTP.CD", countries=("US", "CN"))
        )

        country_codes = {p.country_code for p in result.points}
        self.assertEqual(country_codes, {"US", "CN"})

        cn_points = [p for p in result.points if p.country_code == "CN"]
        self.assertEqual(len(cn_points), 2)
        self.assertEqual(cn_points[0].country_name, "China")
        self.assertAlmostEqual(cn_points[0].value or 0.0, 18532633.0)

    def test_builds_correct_url_and_params(self) -> None:
        self.provider.get_indicator(
            WorldBankQuery(
                indicator="NY.GDP.MKTP.CD",
                countries=("US", "CN"),
                date_range="2020:2024",
                per_page=100,
            )
        )

        self.assertEqual(len(self.fake_client.calls), 1)
        url, params = self.fake_client.calls[0]
        self.assertIn("/country/US;CN/indicator/NY.GDP.MKTP.CD", url)
        assert params is not None
        self.assertEqual(params["format"], "json")
        self.assertEqual(params["date"], "2020:2024")
        self.assertEqual(params["per_page"], 100)


class WorldBankProviderNullValueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeJsonClient(SAMPLE_WITH_NULLS_RESPONSE)
        self.provider = WorldBankProvider(http_client=self.fake_client)

    def test_none_values_preserved(self) -> None:
        result = self.provider.get_indicator(
            WorldBankQuery(indicator="SL.UEM.TOTL.ZS", countries=("US",))
        )

        self.assertEqual(len(result.points), 3)
        self.assertIsNone(result.points[0].value)
        self.assertEqual(result.points[0].date, "2025")

    def test_non_null_values_coerced_to_float(self) -> None:
        result = self.provider.get_indicator(
            WorldBankQuery(indicator="SL.UEM.TOTL.ZS", countries=("US",))
        )

        self.assertAlmostEqual(result.points[1].value or 0.0, 4.1)
        self.assertAlmostEqual(result.points[2].value or 0.0, 3.6)


class WorldBankProviderEmptyDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeJsonClient(SAMPLE_EMPTY_DATA_RESPONSE)
        self.provider = WorldBankProvider(http_client=self.fake_client)

    def test_empty_data_returns_empty_points(self) -> None:
        result = self.provider.get_indicator(
            WorldBankQuery(indicator="FAKE.INDICATOR", countries=("ZZ",))
        )

        self.assertEqual(len(result.points), 0)
        self.assertEqual(result.indicator_id, "FAKE.INDICATOR")
        self.assertEqual(result.indicator_name, "FAKE.INDICATOR")


class WorldBankProviderMetadataTests(unittest.TestCase):
    def test_describe(self) -> None:
        provider = WorldBankProvider(http_client=FakeJsonClient())
        meta = provider.describe()

        self.assertEqual(meta.provider_id, "worldbank")
        self.assertEqual(meta.display_name, "World Bank")
        self.assertEqual(meta.capabilities, ("indicators",))


if __name__ == "__main__":
    unittest.main()
