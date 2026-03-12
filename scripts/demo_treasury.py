from __future__ import annotations

import argparse
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from digital_oracle.providers import ExchangeRateQuery, USTreasuryProvider, YieldCurveQuery


def _print_curve(kind: str, observation_limit: int, year: int | None) -> None:
    provider = USTreasuryProvider()
    query = YieldCurveQuery(curve_kind=kind) if year is None else YieldCurveQuery(year=year, curve_kind=kind)
    observations = provider.list_yield_curve(query)
    print(f"[curve] kind={kind} year={query.year} rows={len(observations)}")
    for observation in observations[:observation_limit]:
        tenors = []
        for tenor in ("2Y", "5Y", "10Y", "30Y"):
            value = observation.yield_for(tenor)
            if value is not None:
                tenors.append(f"{tenor}={value:.2f}%")
        spread_10s2s = observation.spread("10Y", "2Y")
        spread_30s10s = observation.spread("30Y", "10Y")
        print(
            f"  {observation.date} "
            f"{' '.join(tenors)} "
            f"10s2s={spread_10s2s:.2f} "
            f"30s10s={spread_30s10s:.2f}"
            if spread_10s2s is not None and spread_30s10s is not None
            else f"  {observation.date} {' '.join(tenors)}"
        )


def _print_exchange_rates(countries: list[str], limit: int) -> None:
    provider = USTreasuryProvider()
    records = provider.list_exchange_rates(
        ExchangeRateQuery(
            countries=tuple(countries),
            limit=limit,
        )
    )
    print(f"[exchange_rates] rows={len(records)}")
    for record in records:
        print(
            f"  {record.record_date} {record.country_currency_desc} "
            f"rate={record.exchange_rate if record.exchange_rate is not None else 'n/a'}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and normalize U.S. Treasury data.")
    parser.add_argument("--year", type=int, help="Curve year. Defaults to current year.")
    parser.add_argument(
        "--kind",
        choices=("nominal", "real", "bill", "long_term"),
        default="nominal",
        help="Treasury curve type to fetch.",
    )
    parser.add_argument("--limit", type=int, default=3, help="Number of curve rows to print.")
    parser.add_argument(
        "--fx",
        "--fx-country",
        dest="fx_countries",
        action="append",
        default=[],
        help="Country name for FiscalData exchange rates. Repeatable, e.g. China or Japan.",
    )
    parser.add_argument(
        "--fx-limit",
        type=int,
        default=8,
        help="Number of exchange-rate rows to print.",
    )
    args = parser.parse_args()

    _print_curve(args.kind, args.limit, args.year)
    if args.fx_countries:
        _print_exchange_rates(args.fx_countries, args.fx_limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
