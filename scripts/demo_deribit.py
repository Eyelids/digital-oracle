from __future__ import annotations

import argparse
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from digital_oracle.providers import DeribitFuturesCurveQuery, DeribitOptionChainQuery, DeribitProvider


def _format_price(value: float | None, *, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.2f}%"


def _centered_slice(length: int, center: int, limit: int) -> slice:
    if limit <= 0 or length <= limit:
        return slice(0, length)
    start = max(center - limit // 2, 0)
    end = start + limit
    if end > length:
        end = length
        start = end - limit
    return slice(start, end)


def _print_futures_curve(provider: DeribitProvider, *, currency: str) -> None:
    curve = provider.get_futures_term_structure(DeribitFuturesCurveQuery(currency=currency))
    print(f"[deribit futures] currency={curve.currency} points={len(curve.points)}")
    for point in curve.points:
        print(
            f"  {point.instrument_name:<16} mark={_format_price(point.mark_price)} "
            f"mid={_format_price(point.mid_price)} basis={_format_percent(point.basis_vs_perpetual)} "
            f"annualized={_format_percent(point.annualized_basis_vs_perpetual)}"
        )


def _print_option_chain(
    provider: DeribitProvider,
    *,
    currency: str,
    expiration_label: str | None,
    limit: int,
) -> int:
    chain = provider.get_option_chain(
        DeribitOptionChainQuery(currency=currency, expiration_label=expiration_label)
    )
    if chain is None:
        print("option chain not found")
        return 1

    print(
        f"[deribit options] currency={chain.currency} expiry={chain.expiration_label} "
        f"underlying={_format_price(chain.underlying_price)}"
    )
    strikes = list(chain.strikes)
    atm = chain.atm_strike()
    atm_index = strikes.index(atm) if atm is not None else 0
    for strike in strikes[_centered_slice(len(strikes), atm_index, limit)]:
        call_mid = strike.call.mid_price if strike.call else None
        put_mid = strike.put.mid_price if strike.put else None
        call_iv = strike.call.mark_iv if strike.call else None
        put_iv = strike.put.mark_iv if strike.put else None
        print(
            f"  strike={strike.strike:<8.0f} "
            f"call_mid={_format_price(call_mid, digits=4)} call_iv={_format_price(call_iv)} "
            f"put_mid={_format_price(put_mid, digits=4)} put_iv={_format_price(put_iv)}"
        )
    return 0


def _print_order_book(provider: DeribitProvider, *, instrument_name: str, depth: int) -> None:
    book = provider.get_order_book(instrument_name, depth=depth)
    print(
        f"[deribit book] instrument={book.instrument_name} best_bid={_format_price(book.best_bid)} "
        f"best_ask={_format_price(book.best_ask)} spread={_format_price(book.spread)} "
        f"mark={_format_price(book.mark_price)}"
    )
    print("  bids")
    for level in book.bids[: min(5, len(book.bids))]:
        print(f"    price={_format_price(level.price)} size={_format_price(level.size)}")
    print("  asks")
    for level in book.asks[: min(5, len(book.asks))]:
        print(f"    price={_format_price(level.price)} size={_format_price(level.size)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and normalize Deribit derivatives data.")
    parser.add_argument("--currency", default="BTC", help="Base currency such as BTC or ETH.")
    parser.add_argument(
        "--view",
        choices=("futures", "options", "book"),
        default="futures",
        help="Which Deribit view to print.",
    )
    parser.add_argument("--expiration", help="Option expiry label like 27MAR26.")
    parser.add_argument("--instrument", help="Instrument name for --view book.")
    parser.add_argument("--depth", type=int, default=5, help="Order book depth for --view book.")
    parser.add_argument(
        "--limit",
        type=int,
        default=8,
        help="Number of strikes to show around ATM for --view options.",
    )
    args = parser.parse_args()

    provider = DeribitProvider()

    if args.view == "futures":
        _print_futures_curve(provider, currency=args.currency)
        return 0
    if args.view == "options":
        return _print_option_chain(
            provider,
            currency=args.currency,
            expiration_label=args.expiration,
            limit=args.limit,
        )

    instrument_name = args.instrument or f"{args.currency.upper()}-PERPETUAL"
    _print_order_book(provider, instrument_name=instrument_name, depth=args.depth)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
