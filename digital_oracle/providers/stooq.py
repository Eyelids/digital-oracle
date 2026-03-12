from __future__ import annotations

import csv
from dataclasses import dataclass, field
from io import StringIO
from typing import Protocol

from digital_oracle.http import TextHttpClient, UrllibJsonClient

from ._coerce import _coerce_float
from .base import ProviderParseError, SignalProvider
from .prices import PriceBar, PriceHistory, PriceHistoryQuery

STOOQ_HISTORY_URL = "https://stooq.com/q/d/l/"
SUPPORTED_INTERVALS = {"d", "w", "m"}


class StooqHttpClient(TextHttpClient, Protocol):
    pass


def _normalize_symbol(symbol: str) -> str:
    return symbol.strip().lower()


@dataclass
class StooqProvider(SignalProvider):
    provider_id: str = "stooq"
    display_name: str = "Stooq"
    capabilities: tuple[str, ...] = ("price_history",)
    http_client: StooqHttpClient = field(default_factory=UrllibJsonClient)

    def get_history(self, query: PriceHistoryQuery) -> PriceHistory:
        interval = query.interval.lower().strip()
        if interval not in SUPPORTED_INTERVALS:
            raise ValueError(f"unsupported interval: {query.interval}")

        symbol = _normalize_symbol(query.symbol)
        payload = self.http_client.get_text(
            STOOQ_HISTORY_URL,
            params={
                "s": symbol,
                "i": interval,
            },
        )
        return self._parse_history(payload, raw_symbol=query.symbol, symbol=symbol, interval=interval, query=query)

    def _parse_history(
        self,
        payload: str,
        *,
        raw_symbol: str,
        symbol: str,
        interval: str,
        query: PriceHistoryQuery,
    ) -> PriceHistory:
        text = payload.strip()
        if not text:
            raise ProviderParseError("empty Stooq response")
        if text.lower() == "no data":
            return PriceHistory(symbol=symbol, raw_symbol=raw_symbol, interval=interval, provider_id=self.provider_id, bars=())

        reader = csv.DictReader(StringIO(text))
        fieldnames = reader.fieldnames or []
        required_columns = {"Date", "Open", "High", "Low", "Close"}
        if not required_columns.issubset(fieldnames):
            raise ProviderParseError("expected Stooq CSV columns Date/Open/High/Low/Close")

        bars: list[PriceBar] = []
        for row in reader:
            raw_date = row.get("Date")
            if not raw_date:
                continue
            if query.start_date and raw_date < query.start_date:
                continue
            if query.end_date and raw_date > query.end_date:
                continue

            open_price = _coerce_float(row.get("Open"))
            high_price = _coerce_float(row.get("High"))
            low_price = _coerce_float(row.get("Low"))
            close_price = _coerce_float(row.get("Close"))
            if None in (open_price, high_price, low_price, close_price):
                raise ProviderParseError(f"invalid Stooq OHLC row: {row}")

            bars.append(
                PriceBar(
                    date=raw_date,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=_coerce_float(row.get("Volume")),
                )
            )

        if query.limit is not None and query.limit >= 0:
            bars = bars[-query.limit :]

        return PriceHistory(
            symbol=symbol,
            raw_symbol=raw_symbol,
            interval=interval,
            provider_id=self.provider_id,
            bars=tuple(bars),
        )
