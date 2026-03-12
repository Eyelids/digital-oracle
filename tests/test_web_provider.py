"""Tests for digital_oracle.providers.web – WebSearchProvider."""

from __future__ import annotations

import unittest
from dataclasses import dataclass

from digital_oracle.providers.web import (
    WebPageContent,
    WebPageQuery,
    WebSearchProvider,
    WebSearchQuery,
    WebSearchResult,
    WebSearchSnippet,
    _html_to_text,
    _parse_ddg_results,
)


# ---------------------------------------------------------------------------
# Fake HTTP client
# ---------------------------------------------------------------------------


@dataclass
class FakeSearchClient:
    """Returns canned HTML for search and page fetch tests."""

    search_html: str = ""
    page_html: str = ""

    def fetch(self, url: str, *, headers: dict[str, str] | None = None) -> str:
        return self.page_html


# ---------------------------------------------------------------------------
# HTML→text tests
# ---------------------------------------------------------------------------


class TestHtmlToText(unittest.TestCase):
    def test_strips_tags(self):
        html = "<p>Hello <b>world</b></p>"
        text = _html_to_text(html)
        self.assertIn("Hello world", text)

    def test_removes_scripts_and_styles(self):
        html = "<script>var x=1;</script><style>.a{}</style><p>visible</p>"
        text = _html_to_text(html)
        self.assertIn("visible", text)
        self.assertNotIn("var x", text)
        self.assertNotIn(".a{}", text)

    def test_paragraph_breaks(self):
        html = "<p>one</p><p>two</p>"
        text = _html_to_text(html)
        self.assertIn("one", text)
        self.assertIn("two", text)

    def test_empty_html(self):
        self.assertEqual(_html_to_text(""), "")


# ---------------------------------------------------------------------------
# DuckDuckGo result parsing
# ---------------------------------------------------------------------------

SAMPLE_DDG_HTML = """
<div class="result results_links results_links_deep web-result">
  <div class="links_main links_deep result__body">
    <h2 class="result__title">
      <a rel="nofollow" class="result__a" href="https://example.com/page1">
        IMF GDP Forecast 2026
      </a>
    </h2>
    <a class="result__snippet" href="https://example.com/page1">
      The IMF projects global GDP growth of 3.2% in 2026.
    </a>
  </div>
</div>
<div class="result results_links results_links_deep web-result">
  <div class="links_main links_deep result__body">
    <h2 class="result__title">
      <a rel="nofollow" class="result__a" href="https://example.com/page2">
        World Economic Outlook
      </a>
    </h2>
    <a class="result__snippet" href="https://example.com/page2">
      Latest projections from the World Economic Outlook report.
    </a>
  </div>
</div>
"""


class TestDdgParsing(unittest.TestCase):
    def test_parses_result_titles_and_snippets(self):
        results = _parse_ddg_results(SAMPLE_DDG_HTML)
        self.assertGreaterEqual(len(results), 2)

        self.assertIn("IMF GDP Forecast", results[0]["title"])
        self.assertEqual(results[0]["url"], "https://example.com/page1")
        self.assertIn("3.2%", results[0]["snippet"])

        self.assertIn("World Economic Outlook", results[1]["title"])

    def test_empty_html_returns_empty(self):
        self.assertEqual(_parse_ddg_results(""), [])

    def test_no_results_html(self):
        html = "<div class='no-results'>No results found</div>"
        self.assertEqual(_parse_ddg_results(html), [])


# ---------------------------------------------------------------------------
# WebSearchProvider with fakes
# ---------------------------------------------------------------------------


class TestWebSearchProvider(unittest.TestCase):
    def test_fetch_page_extracts_text_and_title(self):
        page_html = """
        <html>
        <head><title>Test Page Title</title></head>
        <body>
            <script>var x = 1;</script>
            <h1>Main Heading</h1>
            <p>This is the body text with <b>bold</b> content.</p>
            <p>Second paragraph here.</p>
        </body>
        </html>
        """
        fake = FakeSearchClient(page_html=page_html)
        provider = WebSearchProvider(http_client=fake)

        result = provider.fetch_page("https://example.com")

        self.assertEqual(result.url, "https://example.com")
        self.assertEqual(result.title, "Test Page Title")
        self.assertIn("Main Heading", result.text)
        self.assertIn("body text", result.text)
        self.assertNotIn("var x", result.text)
        self.assertFalse(result.truncated)

    def test_fetch_page_truncates_long_content(self):
        long_text = "word " * 5000
        page_html = f"<html><head><title>T</title></head><body><p>{long_text}</p></body></html>"
        fake = FakeSearchClient(page_html=page_html)
        provider = WebSearchProvider(http_client=fake)

        result = provider.fetch_page(WebPageQuery(url="https://example.com", max_chars=100))

        self.assertTrue(result.truncated)
        self.assertLessEqual(len(result.text), 100)

    def test_fetch_page_handles_no_title(self):
        fake = FakeSearchClient(page_html="<html><body>Just text</body></html>")
        provider = WebSearchProvider(http_client=fake)

        result = provider.fetch_page("https://example.com")
        self.assertEqual(result.title, "")
        self.assertIn("Just text", result.text)

    def test_search_query_accepts_string(self):
        """WebSearchQuery can be passed as a plain string."""
        q = WebSearchQuery(query="test query", max_results=3)
        self.assertEqual(q.query, "test query")
        self.assertEqual(q.max_results, 3)

    def test_web_search_result_text_rendering(self):
        """WebSearchResult.text() produces readable output."""
        result = WebSearchResult(
            query="IMF GDP",
            snippets=(
                WebSearchSnippet(
                    title="IMF Forecast",
                    url="https://imf.org/weo",
                    snippet="GDP growth 3.2%",
                ),
                WebSearchSnippet(
                    title="World Bank Data",
                    url="https://worldbank.org",
                    snippet="",
                ),
            ),
            fetched_at="2026-03-11T00:00:00+00:00",
        )
        text = result.text()
        self.assertIn("IMF GDP", text)
        self.assertIn("[1] IMF Forecast", text)
        self.assertIn("https://imf.org/weo", text)
        self.assertIn("3.2%", text)
        self.assertIn("[2] World Bank Data", text)


class TestWebSearchProviderDataModels(unittest.TestCase):
    def test_models_are_frozen(self):
        snippet = WebSearchSnippet(title="t", url="u", snippet="s")
        with self.assertRaises(AttributeError):
            snippet.title = "new"  # type: ignore[misc]

        result = WebSearchResult(query="q", snippets=(), fetched_at="2026-01-01")
        with self.assertRaises(AttributeError):
            result.query = "new"  # type: ignore[misc]

        page = WebPageContent(url="u", title="t", text="x", fetched_at="2026-01-01")
        with self.assertRaises(AttributeError):
            page.text = "new"  # type: ignore[misc]

    def test_describe(self):
        provider = WebSearchProvider()
        meta = provider.describe()
        self.assertEqual(meta.provider_id, "web")
        self.assertIn("search", meta.capabilities)
        self.assertIn("fetch_page", meta.capabilities)


if __name__ == "__main__":
    unittest.main()
