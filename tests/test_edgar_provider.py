from __future__ import annotations

import sys
import unittest
from typing import Any, Mapping

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from digital_oracle.providers.edgar import (
    EDGAR_SEARCH_URL,
    EDGAR_SUBMISSIONS_URL,
    EDGAR_TICKERS_URL,
    EdgarInsiderQuery,
    EdgarProvider,
    EdgarSearchQuery,
)
from digital_oracle.providers.base import ProviderError


SAMPLE_TICKERS = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
    "2": {"cik_str": 1318605, "ticker": "TSLA", "title": "Tesla, Inc."},
}

SAMPLE_SUBMISSIONS = {
    "cik": "0000320193",
    "entityType": "operating",
    "sic": "3571",
    "sicDescription": "Electronic Computers",
    "name": "Apple Inc.",
    "tickers": ["AAPL"],
    "filings": {
        "recent": {
            "accessionNumber": [
                "0001140361-26-004321",
                "0000320193-26-000012",
                "0001140361-26-004100",
                "0000320193-26-000011",
                "0001140361-26-003999",
            ],
            "filingDate": [
                "2026-03-05",
                "2026-02-28",
                "2026-02-15",
                "2026-02-01",
                "2026-01-20",
            ],
            "reportDate": [
                "2026-03-03",
                "2025-12-28",
                "2026-02-13",
                "2025-12-28",
                "2026-01-18",
            ],
            "form": ["4", "10-Q", "4", "8-K", "4"],
            "primaryDocument": [
                "xslF345X05/wf-form4_abc.xml",
                "aapl-20251228.htm",
                "xslF345X05/wf-form4_def.xml",
                "aapl-20251228-8k.htm",
                "xslF345X05/wf-form4_ghi.xml",
            ],
            "primaryDocDescription": [
                "4 - APPLE INC (Tim Cook)",
                "10-Q",
                "4 - APPLE INC (Luca Maestri)",
                "8-K",
                "4 - APPLE INC (Jeff Williams)",
            ],
        },
        "files": [],
    },
}

SAMPLE_SEARCH_RESPONSE = {
    "hits": {
        "total": {"value": 42, "relation": "eq"},
        "hits": [
            {
                "_source": {
                    "entity_name": "Apple Inc.",
                    "file_date": "2026-03-05",
                    "form_type": "4",
                    "file_num": "001-36743",
                    "display_names": ["COOK TIMOTHY D"],
                }
            },
            {
                "_source": {
                    "entity_name": "Microsoft Corp",
                    "file_date": "2026-03-01",
                    "form_type": "4",
                    "file_num": "001-37845",
                    "display_names": ["NADELLA SATYA"],
                }
            },
            {
                "_source": {
                    "entity_name": "Tesla, Inc.",
                    "file_date": "2026-02-28",
                    "form_type": "4",
                    "file_num": "001-34756",
                    "display_names": [],
                }
            },
        ],
    }
}


class FakeJsonClient:
    def __init__(
        self,
        *,
        tickers_payload: dict[str, Any] = SAMPLE_TICKERS,
        submissions_payload: dict[str, Any] = SAMPLE_SUBMISSIONS,
        search_payload: dict[str, Any] = SAMPLE_SEARCH_RESPONSE,
    ):
        self.tickers_payload = tickers_payload
        self.submissions_payload = submissions_payload
        self.search_payload = search_payload
        self.calls: list[tuple[str, Mapping[str, object] | None]] = []

    def get_json(self, url: str, *, params: Mapping[str, object] | None = None) -> Any:
        self.calls.append((url, params))
        if url == EDGAR_TICKERS_URL:
            return self.tickers_payload
        if url.startswith(EDGAR_SUBMISSIONS_URL):
            return self.submissions_payload
        if url.startswith(EDGAR_SEARCH_URL) or url == EDGAR_SEARCH_URL:
            return self.search_payload
        raise AssertionError(f"unexpected url: {url}")


class EdgarProviderCIKResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeJsonClient()
        self.provider = EdgarProvider(http_client=self.fake_client)

    def test_resolve_cik_pads_to_ten_digits(self) -> None:
        cik, name = self.provider._resolve_cik("AAPL")
        self.assertEqual(cik, "0000320193")
        self.assertEqual(name, "Apple Inc.")

    def test_resolve_cik_case_insensitive(self) -> None:
        cik, name = self.provider._resolve_cik("aapl")
        self.assertEqual(cik, "0000320193")
        self.assertEqual(name, "Apple Inc.")

    def test_resolve_cik_caches_ticker_map(self) -> None:
        self.provider._resolve_cik("AAPL")
        self.provider._resolve_cik("MSFT")
        # Should only fetch tickers once
        ticker_calls = [url for url, _ in self.fake_client.calls if url == EDGAR_TICKERS_URL]
        self.assertEqual(len(ticker_calls), 1)

    def test_resolve_cik_raises_for_unknown_ticker(self) -> None:
        with self.assertRaises(ProviderError) as ctx:
            self.provider._resolve_cik("ZZZZZ")
        self.assertIn("ticker not found", str(ctx.exception))


class EdgarInsiderTransactionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeJsonClient()
        self.provider = EdgarProvider(http_client=self.fake_client)

    def test_get_insider_transactions_filters_form4s(self) -> None:
        summary = self.provider.get_insider_transactions(
            EdgarInsiderQuery(ticker="AAPL")
        )
        self.assertEqual(summary.ticker, "AAPL")
        self.assertEqual(summary.company_name, "Apple Inc.")
        self.assertEqual(summary.cik, "0000320193")
        self.assertEqual(summary.total_form4_count, 3)
        self.assertEqual(len(summary.recent_form4s), 3)

    def test_form4_filing_fields_are_parsed_correctly(self) -> None:
        summary = self.provider.get_insider_transactions(
            EdgarInsiderQuery(ticker="AAPL")
        )
        first = summary.recent_form4s[0]
        self.assertEqual(first.accession_number, "0001140361-26-004321")
        self.assertEqual(first.form_type, "4")
        self.assertEqual(first.filing_date, "2026-03-05")
        self.assertEqual(first.report_date, "2026-03-03")
        self.assertEqual(first.primary_document, "xslF345X05/wf-form4_abc.xml")
        self.assertEqual(first.description, "4 - APPLE INC (Tim Cook)")

    def test_limit_restricts_number_of_filings_returned(self) -> None:
        summary = self.provider.get_insider_transactions(
            EdgarInsiderQuery(ticker="AAPL", limit=2)
        )
        self.assertEqual(len(summary.recent_form4s), 2)
        # total_form4_count should still reflect all Form 4s
        self.assertEqual(summary.total_form4_count, 3)

    def test_non_form4_filings_are_excluded(self) -> None:
        summary = self.provider.get_insider_transactions(
            EdgarInsiderQuery(ticker="AAPL")
        )
        for filing in summary.recent_form4s:
            self.assertEqual(filing.form_type, "4")

    def test_submissions_url_uses_padded_cik(self) -> None:
        self.provider.get_insider_transactions(
            EdgarInsiderQuery(ticker="AAPL")
        )
        submissions_calls = [
            url for url, _ in self.fake_client.calls
            if url.startswith(EDGAR_SUBMISSIONS_URL) and url != EDGAR_TICKERS_URL
        ]
        self.assertEqual(len(submissions_calls), 1)
        self.assertEqual(
            submissions_calls[0],
            f"{EDGAR_SUBMISSIONS_URL}/CIK0000320193.json",
        )

    def test_ticker_normalization_uppercase(self) -> None:
        summary = self.provider.get_insider_transactions(
            EdgarInsiderQuery(ticker="aapl")
        )
        self.assertEqual(summary.ticker, "AAPL")


class EdgarSearchFilingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeJsonClient()
        self.provider = EdgarProvider(http_client=self.fake_client)

    def test_search_filings_returns_hits(self) -> None:
        results = self.provider.search_filings(
            EdgarSearchQuery(query="insider purchase", forms="4")
        )
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].entity_name, "Apple Inc.")
        self.assertEqual(results[0].file_date, "2026-03-05")
        self.assertEqual(results[0].form_type, "4")
        self.assertEqual(results[0].file_number, "001-36743")

    def test_search_filings_passes_params(self) -> None:
        self.provider.search_filings(
            EdgarSearchQuery(
                query="quarterly report",
                forms="10-Q",
                date_start="2025-01-01",
                date_end="2026-03-11",
            )
        )
        search_calls = [
            (url, params) for url, params in self.fake_client.calls
            if url == EDGAR_SEARCH_URL
        ]
        self.assertEqual(len(search_calls), 1)
        _, params = search_calls[0]
        self.assertIsNotNone(params)
        assert params is not None
        self.assertEqual(params["q"], "quarterly report")
        self.assertEqual(params["forms"], "10-Q")
        self.assertEqual(params["dateRange"], "custom")
        self.assertEqual(params["startdt"], "2025-01-01")
        self.assertEqual(params["enddt"], "2026-03-11")

    def test_search_filings_limit_restricts_results(self) -> None:
        results = self.provider.search_filings(
            EdgarSearchQuery(query="test", limit=2)
        )
        self.assertEqual(len(results), 2)

    def test_search_filings_empty_display_names_handled(self) -> None:
        results = self.provider.search_filings(
            EdgarSearchQuery(query="test", limit=10)
        )
        # Third hit has empty display_names list
        self.assertEqual(results[2].entity_name, "Tesla, Inc.")
        self.assertEqual(results[2].description, "")

    def test_search_filings_no_date_range_omits_params(self) -> None:
        self.provider.search_filings(
            EdgarSearchQuery(query="test")
        )
        search_calls = [
            (url, params) for url, params in self.fake_client.calls
            if url == EDGAR_SEARCH_URL
        ]
        _, params = search_calls[0]
        assert params is not None
        self.assertNotIn("dateRange", params)
        self.assertNotIn("startdt", params)
        self.assertNotIn("enddt", params)


class EdgarProviderMetadataTests(unittest.TestCase):
    def test_provider_metadata(self) -> None:
        provider = EdgarProvider(http_client=FakeJsonClient())
        meta = provider.describe()
        self.assertEqual(meta.provider_id, "sec_edgar")
        self.assertEqual(meta.display_name, "SEC EDGAR")
        self.assertIn("insider_transactions", meta.capabilities)
        self.assertIn("filings_search", meta.capabilities)


if __name__ == "__main__":
    unittest.main()
