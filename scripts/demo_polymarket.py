from __future__ import annotations

import argparse
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from digital_oracle.providers import PolymarketEvent, PolymarketEventQuery, PolymarketProvider


def _format_probability(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def _print_market_snapshot(event: PolymarketEvent) -> None:
    market = event.primary_market()
    print(f"[event] {event.title} ({event.slug})")
    print(
        f"  active={event.active} closed={event.closed} volume24h={event.volume_24hr or 0:.0f} "
        f"liquidity={event.liquidity or 0:.0f}"
    )
    if not market:
        print("  no nested markets")
        return

    print(f"  [market] {market.question}")
    print(
        f"  yes={_format_probability(market.yes_probability)} "
        f"best_bid={market.best_bid if market.best_bid is not None else 'n/a'} "
        f"best_ask={market.best_ask if market.best_ask is not None else 'n/a'} "
        f"last={market.last_trade_price if market.last_trade_price is not None else 'n/a'}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and normalize Polymarket events.")
    parser.add_argument("--slug", help="Exact event slug to fetch.")
    parser.add_argument("--search", help="Partial slug search using slug_contains.")
    parser.add_argument("--limit", type=int, default=5, help="Number of events to print.")
    parser.add_argument(
        "--include-closed",
        action="store_true",
        help="Include closed events when listing events.",
    )
    parser.add_argument(
        "--show-book",
        action="store_true",
        help="Fetch the YES order book for the event's primary market when possible.",
    )
    args = parser.parse_args()

    provider = PolymarketProvider()

    if args.slug:
        event = provider.get_event(args.slug)
        if not event:
            print("event not found")
            return 1
        _print_market_snapshot(event)
        if args.show_book:
            market = event.primary_market()
            token_id = market.token_id_for("yes") if market else None
            if token_id:
                book = provider.get_order_book(token_id)
                print(
                    f"  [orderbook] best_bid={book.best_bid} best_ask={book.best_ask} "
                    f"spread={book.spread} levels={len(book.bids)}/{len(book.asks)}"
                )
        return 0

    events = provider.list_events(
        PolymarketEventQuery(
            limit=args.limit,
            active=None if args.include_closed else True,
            closed=None if args.include_closed else False,
            slug_contains=args.search,
        )
    )
    for event in events:
        _print_market_snapshot(event)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
