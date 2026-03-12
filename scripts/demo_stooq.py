from __future__ import annotations

import argparse
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from digital_oracle.providers import PriceHistoryQuery, StooqProvider


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and normalize Stooq price history.")
    parser.add_argument("--symbol", default="spy.us", help="Stooq symbol, e.g. spy.us, aapl.us, eurusd.")
    parser.add_argument(
        "--interval",
        choices=("d", "w", "m"),
        default="d",
        help="History interval: daily, weekly, monthly.",
    )
    parser.add_argument("--limit", type=int, default=5, help="Number of trailing bars to print.")
    parser.add_argument("--start-date", help="Optional inclusive start date, YYYY-MM-DD.")
    parser.add_argument("--end-date", help="Optional inclusive end date, YYYY-MM-DD.")
    args = parser.parse_args()

    provider = StooqProvider()
    history = provider.get_history(
        PriceHistoryQuery(
            symbol=args.symbol,
            interval=args.interval,
            start_date=args.start_date,
            end_date=args.end_date,
            limit=args.limit,
        )
    )

    print(
        f"[history] symbol={history.symbol} raw_symbol={history.raw_symbol} "
        f"interval={history.interval} bars={len(history.bars)}"
    )
    for bar in history.bars:
        volume = "n/a" if bar.volume is None else f"{bar.volume:.0f}"
        print(
            f"  {bar.date} o={bar.open:.4f} h={bar.high:.4f} "
            f"l={bar.low:.4f} c={bar.close:.4f} v={volume}"
        )

    latest = history.latest
    if latest is not None:
        print(f"[latest] {latest.date} close={latest.close:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
