"""Web search provider – fetches search snippets and page text via DuckDuckGo.

Zero API keys required.  Uses DuckDuckGo HTML endpoint for search results
and plain urllib for page fetching.  All parsing uses stdlib only
(``html.parser``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .base import ProviderError, SignalProvider

# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------


class SearchHttpClient(Protocol):
    """Minimal HTTP surface needed by :class:`WebSearchProvider`."""

    def fetch(self, url: str, *, headers: dict[str, str] | None = None) -> str:
        """GET *url* and return the response body as text."""
        ...


# ---------------------------------------------------------------------------
# Default HTTP implementation (stdlib only)
# ---------------------------------------------------------------------------


@dataclass
class UrllibSearchClient:
    """urllib-based implementation of :class:`SearchHttpClient`."""

    timeout_seconds: float = 20.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    user_agent: str = "predict-by-emh/0.1"

    def fetch(self, url: str, *, headers: dict[str, str] | None = None) -> str:
        hdrs = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if headers:
            hdrs.update(headers)
        req = Request(url, headers=hdrs)
        import time

        last_error: Exception | None = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                with urlopen(req, timeout=self.timeout_seconds) as resp:
                    charset = resp.headers.get_content_charset() or "utf-8"
                    return resp.read().decode(charset, errors="replace")
            except HTTPError:
                raise
            except (URLError, TimeoutError) as exc:
                last_error = exc
                if attempt >= self.retry_attempts:
                    break
                time.sleep(self.retry_delay_seconds)
        raise ProviderError(f"web fetch failed: {url}") from last_error


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------


class _TagStripper(HTMLParser):
    """Minimal HTML → plain-text converter."""

    def __init__(self) -> None:
        super().__init__()
        self._pieces: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = False
        if tag in ("p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._pieces.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self._pieces.append(data)

    def get_text(self) -> str:
        raw = "".join(self._pieces)
        # Collapse whitespace but preserve paragraph breaks.
        lines = (line.strip() for line in raw.splitlines())
        return "\n".join(line for line in lines if line)


def _html_to_text(html: str) -> str:
    parser = _TagStripper()
    parser.feed(html)
    return parser.get_text()


class _DuckDuckGoParser(HTMLParser):
    """Extract search result snippets from DuckDuckGo HTML response."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._current: dict[str, str] = {}
        self._capture: str | None = None  # "title" or "snippet"
        self._depth = 0
        self._in_result = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        cls = attr_dict.get("class", "") or ""

        # New result block → flush the previous one
        if tag == "a" and "result__a" in cls:
            self._flush()
            href = attr_dict.get("href", "")
            if href:
                self._current["url"] = href
            self._capture = "title"
            self._current.setdefault("title", "")

        # Snippet
        if tag == "a" and "result__snippet" in cls:
            self._capture = "snippet"
            self._current.setdefault("snippet", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._capture in ("title", "snippet"):
            self._capture = None

    def handle_data(self, data: str) -> None:
        if self._capture == "title":
            self._current["title"] = self._current.get("title", "") + data
        elif self._capture == "snippet":
            self._current["snippet"] = self._current.get("snippet", "") + data

    def _flush(self) -> None:
        if self._current.get("url") and self._current.get("title"):
            self.results.append(self._current)
            self._current = {}

    def close(self) -> None:
        self._flush()
        super().close()


def _parse_ddg_results(html: str) -> list[dict[str, str]]:
    """Parse DuckDuckGo HTML results into a list of {title, url, snippet}."""
    parser = _DuckDuckGoParser()
    parser.feed(html)
    parser.close()

    # Fallback: regex-based extraction if parser found nothing
    if not parser.results:
        results: list[dict[str, str]] = []
        # DuckDuckGo result links
        for m in re.finditer(
            r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            html,
            re.DOTALL,
        ):
            url, title_html = m.group(1), m.group(2)
            title = re.sub(r"<[^>]+>", "", title_html).strip()
            if url and title:
                results.append({"url": url, "title": title, "snippet": ""})

        # Try to attach snippets
        for i, m in enumerate(
            re.finditer(
                r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
                html,
                re.DOTALL,
            )
        ):
            snippet = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            if i < len(results):
                results[i]["snippet"] = snippet

        return results

    return parser.results


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WebSearchQuery:
    """Query for :meth:`WebSearchProvider.search`."""

    query: str
    max_results: int = 5


@dataclass(frozen=True)
class WebSearchSnippet:
    """One search result snippet."""

    title: str
    url: str
    snippet: str


@dataclass(frozen=True)
class WebSearchResult:
    """Container for search results."""

    query: str
    snippets: tuple[WebSearchSnippet, ...]
    fetched_at: str  # ISO-8601

    def text(self) -> str:
        """Render search results as a readable text block for LLM consumption."""
        lines = [f'Search: "{self.query}"', ""]
        for i, s in enumerate(self.snippets, 1):
            lines.append(f"[{i}] {s.title}")
            lines.append(f"    {s.url}")
            if s.snippet:
                lines.append(f"    {s.snippet}")
            lines.append("")
        return "\n".join(lines)


@dataclass(frozen=True)
class WebPageQuery:
    """Query for :meth:`WebSearchProvider.fetch_page`."""

    url: str
    max_chars: int = 8000


@dataclass(frozen=True)
class WebPageContent:
    """Extracted text from a web page."""

    url: str
    title: str
    text: str
    fetched_at: str  # ISO-8601
    truncated: bool = False


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

DDG_HTML_URL = "https://html.duckduckgo.com/html/"


class WebSearchProvider(SignalProvider):
    """Search the web and fetch page content.  Zero API keys required.

    Uses DuckDuckGo HTML search for snippets and plain urllib for page text.
    """

    provider_id = "web"
    display_name = "Web Search"
    capabilities = ("search", "fetch_page")

    def __init__(self, http_client: SearchHttpClient | None = None) -> None:
        self.http_client = http_client or UrllibSearchClient()

    # -- search ------------------------------------------------------------

    def search(self, query: WebSearchQuery | str) -> WebSearchResult:
        """Run a web search and return result snippets."""
        if isinstance(query, str):
            query = WebSearchQuery(query=query)

        form_data = urlencode({"q": query.query}).encode("utf-8")
        req = Request(
            DDG_HTML_URL,
            data=form_data,
            headers={
                "User-Agent": "predict-by-emh/0.1",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html",
                "Accept-Language": "en-US,en;q=0.9",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=20.0) as resp:
                html = resp.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ProviderError(f"web search failed for: {query.query}") from exc

        raw_results = _parse_ddg_results(html)
        snippets = tuple(
            WebSearchSnippet(
                title=r.get("title", "").strip(),
                url=r.get("url", "").strip(),
                snippet=r.get("snippet", "").strip(),
            )
            for r in raw_results[: query.max_results]
            if r.get("url")
        )

        return WebSearchResult(
            query=query.query,
            snippets=snippets,
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )

    # -- fetch_page --------------------------------------------------------

    def fetch_page(self, query: WebPageQuery | str) -> WebPageContent:
        """Fetch a URL and extract its text content."""
        if isinstance(query, str):
            query = WebPageQuery(url=query)

        html = self.http_client.fetch(query.url)

        # Extract <title>
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else ""

        text = _html_to_text(html)
        truncated = False
        if len(text) > query.max_chars:
            text = text[: query.max_chars]
            truncated = True

        return WebPageContent(
            url=query.url,
            title=title,
            text=text,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            truncated=truncated,
        )
