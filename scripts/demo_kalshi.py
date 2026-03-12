from __future__ import annotations

import argparse
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from digital_oracle.providers import KalshiMarketQuery, KalshiProvider


def _format_probability(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def _print_market(market) -> None:
    print(f"[market] {market.title}")
    print(f"  ticker={market.ticker} event={market.event_ticker} status={market.status}")
    print(
        f"  yes_bid={_format_probability(market.yes_bid)} "
        f"yes_ask={_format_probability(market.yes_ask)} "
        f"last={_format_probability(market.last_price)} "
        f"volume={market.volume or 0:.0f} oi={market.open_interest or 0:.0f}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and normalize Kalshi events and markets.")
    parser.add_argument("--series", default="KXFED", help="Kalshi series ticker to list.")
    parser.add_argument("--event", help="Event ticker to fetch.")
    parser.add_argument("--ticker", help="Market ticker to fetch.")
    parser.add_argument("--limit", type=int, default=5, help="Number of markets to print when listing.")
    parser.add_argument(
        "--show-book",
        action="store_true",
        help="Fetch the order book for the selected market.",
    )
    parser.add_argument("--depth", type=int, default=10, help="Order book depth when --show-book is used.")
    args = parser.parse_args()

    provider = KalshiProvider()

    market = None
    if args.ticker:
        market = provider.get_market(args.ticker)
        _print_market(market)
    elif args.event:
        event = provider.get_event(args.event)
        print(f"[event] {event.title} ({event.event_ticker}) category={event.category or 'n/a'}")
        print(f"  series={event.series_ticker} markets={len(event.markets)}")
        for market in event.markets[: args.limit]:
            _print_market(market)
    else:
        markets = provider.list_markets(
            KalshiMarketQuery(limit=args.limit, status="open", series_ticker=args.series)
        )
        for market in markets:
            _print_market(market)
        if markets:
            market = markets[0]

    if args.show_book and market is not None:
        book = provider.get_order_book(market.ticker, depth=args.depth)
        print(
            f"  [orderbook] best_yes_bid={_format_probability(book.best_yes_bid)} "
            f"best_yes_ask={_format_probability(book.best_yes_ask)} "
            f"spread={_format_probability(book.yes_spread)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
