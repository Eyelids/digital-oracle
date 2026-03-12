#!/usr/bin/env python3
"""Regression test runner: run full digital-oracle workflow on real topics.

Usage: python3 scripts/regression_runner.py <test_number>
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from digital_oracle import (
    PolymarketProvider, PolymarketEventQuery,
    KalshiProvider, KalshiMarketQuery,
    StooqProvider, PriceHistoryQuery,
    DeribitProvider, DeribitFuturesCurveQuery, DeribitOptionChainQuery,
    USTreasuryProvider, YieldCurveQuery,
    WebSearchProvider,
    CftcCotProvider, CftcCotQuery,
    CoinGeckoProvider, CoinGeckoPriceQuery,
    BisProvider, BisRateQuery,
    WorldBankProvider, WorldBankQuery,
    EdgarProvider, EdgarInsiderQuery,
    gather,
)

# ── providers (reused across tests) ──
pm = PolymarketProvider()
kalshi = KalshiProvider()
stooq = StooqProvider()
deribit = DeribitProvider()
treasury = USTreasuryProvider()
web = WebSearchProvider()
cftc = CftcCotProvider()
coingecko = CoinGeckoProvider()
bis = BisProvider()
wb = WorldBankProvider()
edgar = EdgarProvider(user_email="eyelidstl@gmail.com")


def run_test(name: str, tasks: dict) -> dict:
    """Run a gather() call, print results summary, return stats."""
    print(f"\n{'='*70}")
    print(f"  TEST: {name}")
    print(f"{'='*70}")

    result = gather(tasks, timeout_seconds=45, max_workers=8)

    stats = {"name": name, "ok": 0, "fail": 0, "errors": {}}
    for key in sorted(tasks.keys()):
        val = result.get_or(key, "__FAIL__")
        if val == "__FAIL__":
            err = result.errors.get(key)
            err_str = f"{type(err).__name__}: {err}" if err else "unknown"
            stats["errors"][key] = err_str
            stats["fail"] += 1
            print(f"  ✗ {key}: {err_str}")
        else:
            stats["ok"] += 1
            # Print a short summary of the result
            summary = _summarize(key, val)
            print(f"  ✓ {key}: {summary}")

    print(f"\n  Result: {stats['ok']}/{stats['ok']+stats['fail']} succeeded")
    return stats


def _summarize(key: str, val) -> str:
    """Create a one-line summary of any result type."""
    if val is None:
        return "None"
    t = type(val).__name__

    # Lists
    if isinstance(val, list):
        if not val:
            return f"{t}(empty)"
        first = val[0]
        ft = type(first).__name__
        # Try to get a title/name
        title = getattr(first, 'title', None) or getattr(first, 'market_name', None) or getattr(first, 'coin_id', None) or ""
        if title:
            return f"{t}[{len(val)}] first={ft}('{title}')"
        return f"{t}[{len(val)}] of {ft}"

    # PriceHistory
    if hasattr(val, 'bars') and hasattr(val, 'symbol'):
        bars = val.bars
        if bars:
            return f"PriceHistory({val.symbol}, {len(bars)} bars, {bars[0].date}~{bars[-1].date}, latest={bars[-1].close})"
        return f"PriceHistory({val.symbol}, 0 bars)"

    # YieldCurveSnapshot
    if hasattr(val, 'points') and hasattr(val, 'curve_kind'):
        return f"YieldCurve({val.date}, {len(val.points)} tenors)"

    # DeribitFuturesTermStructure
    if hasattr(val, 'points') and hasattr(val, 'currency'):
        return f"FuturesCurve({val.currency}, {len(val.points)} points)"

    # OptionsChain
    if hasattr(val, 'contracts') and hasattr(val, 'ticker'):
        return f"OptionsChain({val.ticker}, {len(val.contracts)} contracts, atm_iv={val.atm_iv})"

    # WebSearchResult
    if hasattr(val, 'snippets') and hasattr(val, 'query'):
        q = val.query if isinstance(val.query, str) else getattr(val.query, 'query', '')
        return f"WebSearch('{q[:40]}', {len(val.snippets)} results)"

    # WorldBankResult
    if hasattr(val, 'points') and hasattr(val, 'indicator_id'):
        return f"WorldBank({val.indicator_id}, {len(val.points)} points)"

    # EdgarInsiderSummary
    if hasattr(val, 'recent_form4s'):
        return f"Edgar({val.ticker}, {len(val.recent_form4s)} form4s)"

    # CoinGeckoGlobal
    if hasattr(val, 'btc_dominance_pct'):
        return f"CryptoGlobal(btc_dom={val.btc_dominance_pct:.1f}%, cap={val.total_market_cap_usd/1e12:.2f}T)"

    # Fallback
    return f"{t}(...)"


# ═══════════════════════════════════════════════════════════════
# 10 TEST CASES
# ═══════════════════════════════════════════════════════════════

TESTS = {}

# ── Test 1: 美国经济衰退概率 ──
TESTS[1] = ("Will the US enter a recession in 2026?", {
    "pm_recession": lambda: pm.list_events(PolymarketEventQuery(slug_contains="recession", limit=5)),
    "kalshi_recession": lambda: kalshi.list_markets(KalshiMarketQuery(series_ticker="USRECESSION")),
    "yield_curve": lambda: treasury.latest_yield_curve(),
    "spy": lambda: stooq.get_history(PriceHistoryQuery(symbol="spy.us", limit=30)),
    "copper": lambda: stooq.get_history(PriceHistoryQuery(symbol="hg.c", limit=30)),
    "gold": lambda: stooq.get_history(PriceHistoryQuery(symbol="xauusd", limit=30)),
    "copper_cot": lambda: cftc.list_reports(CftcCotQuery(commodity_name="COPPER", limit=4)),
    "btc": lambda: coingecko.get_prices(CoinGeckoPriceQuery(coin_ids=("bitcoin",))),
    "gdp": lambda: wb.get_indicator(WorldBankQuery(indicator="NY.GDP.MKTP.KD.ZG", countries=("US",))),
    "vix": lambda: web.search("VIX index current level"),
    "hy_spread": lambda: web.search("US high yield bond spread OAS current"),
})

# ── Test 2: AI 是否在泡沫中？ ──
TESTS[2] = ("Is AI in a bubble?", {
    "pm_ai": lambda: pm.list_events(PolymarketEventQuery(slug_contains="artificial-intelligence", limit=5)),
    "nvda": lambda: stooq.get_history(PriceHistoryQuery(symbol="nvda.us", limit=60)),
    "smh": lambda: stooq.get_history(PriceHistoryQuery(symbol="smh.us", limit=60)),
    "msft": lambda: stooq.get_history(PriceHistoryQuery(symbol="msft.us", limit=60)),
    "googl": lambda: stooq.get_history(PriceHistoryQuery(symbol="googl.us", limit=60)),
    "nvda_insider": lambda: edgar.get_insider_transactions(EdgarInsiderQuery(ticker="NVDA", limit=10)),
    "asml": lambda: web.search("ASML orders backlog 2026 semiconductor equipment"),
    "ai_capex": lambda: web.search("big tech AI capital expenditure 2026 spending"),
    "gpu_rental": lambda: web.search("GPU cloud rental price H100 2026"),
})

# ── Test 3: 台海风险 ──
TESTS[3] = ("Will China invade Taiwan in the next 3 years?", {
    "pm_taiwan": lambda: pm.list_events(PolymarketEventQuery(slug_contains="taiwan", limit=5)),
    "pm_china_war": lambda: pm.list_events(PolymarketEventQuery(slug_contains="china-war", limit=5)),
    "usdcny": lambda: stooq.get_history(PriceHistoryQuery(symbol="usdcny", limit=60)),
    "usdtwd": lambda: stooq.get_history(PriceHistoryQuery(symbol="usdtwd", limit=60)),
    "tsm": lambda: stooq.get_history(PriceHistoryQuery(symbol="tsm.us", limit=60)),
    "fxi": lambda: stooq.get_history(PriceHistoryQuery(symbol="fxi.us", limit=60)),
    "gold": lambda: stooq.get_history(PriceHistoryQuery(symbol="xauusd", limit=30)),
    "defense": lambda: stooq.get_history(PriceHistoryQuery(symbol="lmt.us", limit=30)),
    "bis_cn": lambda: bis.get_policy_rates(BisRateQuery(countries=("CN",), start_year=2024)),
    "china_gdp": lambda: wb.get_indicator(WorldBankQuery(indicator="NY.GDP.MKTP.KD.ZG", countries=("CN",))),
    "taiwan_risk": lambda: web.search("Taiwan strait military tension 2026"),
})

# ── Test 4: 现在该买比特币吗？ ──
TESTS[4] = ("Should I buy Bitcoin now?", {
    "btc_price": lambda: coingecko.get_prices(CoinGeckoPriceQuery(coin_ids=("bitcoin",))),
    "crypto_global": lambda: coingecko.get_global(),
    "btc_futures": lambda: deribit.get_futures_term_structure(DeribitFuturesCurveQuery(currency="BTC")),
    "btc_options": lambda: deribit.get_option_chain(DeribitOptionChainQuery(currency="BTC")),
    "pm_btc": lambda: pm.list_events(PolymarketEventQuery(slug_contains="bitcoin", limit=5)),
    "kalshi_btc": lambda: kalshi.list_markets(KalshiMarketQuery(series_ticker="KXBTC")),
    "spy": lambda: stooq.get_history(PriceHistoryQuery(symbol="spy.us", limit=30)),
    "dxy": lambda: web.search("US dollar index DXY current level"),
    "fed": lambda: web.search("Federal Reserve interest rate decision 2026"),
})

# ── Test 5: 原油价格走向 ──
TESTS[5] = ("Where is oil price headed?", {
    "oil": lambda: stooq.get_history(PriceHistoryQuery(symbol="cl.c", limit=60)),
    "ng": lambda: stooq.get_history(PriceHistoryQuery(symbol="ng.c", limit=30)),
    "oil_cot": lambda: cftc.list_reports(CftcCotQuery(commodity_name="CRUDE OIL", limit=4)),
    "xom": lambda: stooq.get_history(PriceHistoryQuery(symbol="xom.us", limit=30)),
    "pm_oil": lambda: pm.list_events(PolymarketEventQuery(slug_contains="crude-oil", limit=5)),
    "kalshi_oil": lambda: kalshi.list_markets(KalshiMarketQuery(series_ticker="KXOILP")),
    "opec": lambda: web.search("OPEC production cuts 2026 oil supply"),
    "strait": lambda: web.search("Strait of Hormuz Iran oil shipping 2026"),
})

# ── Test 6: 美联储利率路径 ──
TESTS[6] = ("What will the Fed do with rates in 2026?", {
    "pm_fed": lambda: pm.list_events(PolymarketEventQuery(slug_contains="fed-decision", limit=5)),
    "kalshi_fed": lambda: kalshi.list_markets(KalshiMarketQuery(series_ticker="FED")),
    "yield_curve": lambda: treasury.latest_yield_curve(),
    "rates_us": lambda: bis.get_policy_rates(BisRateQuery(countries=("US",), start_year=2023)),
    "spy": lambda: stooq.get_history(PriceHistoryQuery(symbol="spy.us", limit=30)),
    "gold": lambda: stooq.get_history(PriceHistoryQuery(symbol="xauusd", limit=30)),
    "tlt": lambda: stooq.get_history(PriceHistoryQuery(symbol="tlt.us", limit=30)),
    "dxy": lambda: web.search("US dollar index DXY current level"),
    "fed_minutes": lambda: web.search("FOMC minutes March 2026 rate decision"),
})

# ── Test 7: NVIDIA 期权是否过贵？ ──
TESTS[7] = ("Is NVDA options premium overpriced?", {
    "nvda": lambda: stooq.get_history(PriceHistoryQuery(symbol="nvda.us", limit=60)),
    "nvda_insider": lambda: edgar.get_insider_transactions(EdgarInsiderQuery(ticker="NVDA", limit=10)),
    "smh": lambda: stooq.get_history(PriceHistoryQuery(symbol="smh.us", limit=30)),
    "spy": lambda: stooq.get_history(PriceHistoryQuery(symbol="spy.us", limit=30)),
    "nvda_news": lambda: web.search("NVIDIA earnings guidance 2026 Q1"),
    "ai_demand": lambda: web.search("AI chip demand H100 B200 2026"),
})

# ── Test 8: 俄乌战争何时结束？ ──
TESTS[8] = ("When will the Russia-Ukraine war end?", {
    "pm_ukraine": lambda: pm.list_events(PolymarketEventQuery(slug_contains="ukraine", limit=10)),
    "pm_ceasefire": lambda: pm.list_events(PolymarketEventQuery(slug_contains="ceasefire", limit=5)),
    "wheat": lambda: stooq.get_history(PriceHistoryQuery(symbol="zw.c", limit=30)),
    "ng_eu": lambda: web.search("TTF natural gas price Europe 2026"),
    "usdrub": lambda: stooq.get_history(PriceHistoryQuery(symbol="usdrub", limit=30)),
    "gold": lambda: stooq.get_history(PriceHistoryQuery(symbol="xauusd", limit=30)),
    "defense": lambda: stooq.get_history(PriceHistoryQuery(symbol="ita.us", limit=30)),
    "bis_ru": lambda: bis.get_policy_rates(BisRateQuery(countries=("RU",), start_year=2024)),
    "ceasefire_news": lambda: web.search("Russia Ukraine ceasefire negotiations 2026"),
})

# ── Test 9: 黄金还能涨吗？ ──
TESTS[9] = ("Can gold keep rallying from $5000?", {
    "gold": lambda: stooq.get_history(PriceHistoryQuery(symbol="xauusd", limit=90)),
    "silver": lambda: stooq.get_history(PriceHistoryQuery(symbol="xagusd", limit=60)),
    "gold_cot": lambda: cftc.list_reports(CftcCotQuery(commodity_name="GOLD", limit=8)),
    "gdx": lambda: stooq.get_history(PriceHistoryQuery(symbol="gdx.us", limit=60)),
    "dxy": lambda: web.search("US dollar index DXY current level"),
    "yield_curve": lambda: treasury.latest_yield_curve(),
    "bis_rates": lambda: bis.get_policy_rates(BisRateQuery(countries=("US", "CN"), start_year=2024)),
    "pm_gold": lambda: pm.list_events(PolymarketEventQuery(slug_contains="gold-price", limit=5)),
    "central_bank_gold": lambda: web.search("central bank gold buying 2026 reserves"),
})

# ── Test 10: 2028 美国大选谁赢？ ──
TESTS[10] = ("Who will win the 2028 US presidential election?", {
    "pm_2028": lambda: pm.list_events(PolymarketEventQuery(slug_contains="president-2028", limit=5)),
    "pm_nominee_r": lambda: pm.list_events(PolymarketEventQuery(slug_contains="republican-nominee-2028", limit=5)),
    "pm_nominee_d": lambda: pm.list_events(PolymarketEventQuery(slug_contains="democrat-nominee-2028", limit=5)),
    "kalshi_2028": lambda: kalshi.list_markets(KalshiMarketQuery(series_ticker="PRES2028")),
    "spy": lambda: stooq.get_history(PriceHistoryQuery(symbol="spy.us", limit=30)),
    "approval": lambda: web.search("Trump approval rating March 2026"),
    "polls": lambda: web.search("2028 presidential election polls early"),
})


def main():
    if len(sys.argv) < 2:
        print("Available tests:")
        for n, (title, _) in TESTS.items():
            print(f"  {n}: {title}")
        print(f"\nUsage: python3 {sys.argv[0]} <test_number>")
        print(f"       python3 {sys.argv[0]} all")
        return

    arg = sys.argv[1]
    if arg == "all":
        test_numbers = sorted(TESTS.keys())
    else:
        test_numbers = [int(arg)]

    all_stats = []
    for n in test_numbers:
        if n not in TESTS:
            print(f"Unknown test: {n}")
            continue
        title, tasks = TESTS[n]
        try:
            stats = run_test(f"#{n} {title}", tasks)
            all_stats.append(stats)
        except Exception as exc:
            print(f"\n  FATAL: {type(exc).__name__}: {exc}")
            traceback.print_exc()
            all_stats.append({"name": f"#{n} {title}", "ok": 0, "fail": -1, "errors": {"FATAL": str(exc)}})

    # Summary
    if len(all_stats) > 1:
        print(f"\n{'='*70}")
        print(f"  SUMMARY: {len(all_stats)} tests")
        print(f"{'='*70}")
        total_ok = total_fail = 0
        for s in all_stats:
            total_ok += s["ok"]
            total_fail += max(s["fail"], 0)
            status = "✓" if s["fail"] == 0 else "✗"
            print(f"  {status} {s['name']}: {s['ok']}/{s['ok']+max(s['fail'],0)}")
            for k, v in s["errors"].items():
                print(f"      ✗ {k}: {v}")
        print(f"\n  Total: {total_ok}/{total_ok+total_fail} calls succeeded")


if __name__ == "__main__":
    main()
