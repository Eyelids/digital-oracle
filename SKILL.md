---
name: digital-oracle
version: 1.0.1
description: "Answer prediction questions using market trading data, not opinions. Use when the user asks probability questions about geopolitics, economics, markets, industries, or any topic where real money is being traded on the outcome. Examples: 'What's the probability of WW3?', 'Will there be a recession?', 'Is AI in a bubble?', 'When will the Russia-Ukraine war end?', 'Is it a good time to buy gold?', 'Will SPY drop 5% this month?', 'Is NVDA options premium overpriced?'. The skill reads prices from prediction markets, commodities, equities, options chains, derivatives, yield curves, and currencies, then cross-validates multiple signals to produce a structured probability report."
metadata: { "openclaw": { "emoji": "📈", "requires": { "bins": ["uv"] } } }
---

# digital-oracle

> Markets are efficient. Price contains all public information. Reading price = reading market consensus.

## Methodology

**Answer questions using only market trading data — no news, opinions, or statistical reports as causal evidence.** If something is true, some market has already priced it in.

Five iron rules:

1. **Trading data only** — prices, volume, open interest, spreads, premiums. Never cite analyst opinions.
2. **Explicit reasoning from price to judgment** — explain clearly "why this price answers this question."
3. **Multi-signal cross-validation** — never conclude from a single signal. At least 3 independent dimensions.
4. **Label the time horizon of each signal** — options price 3 months, equipment orders price 3 years — don't mix them in the same vote.
5. **Structured output** — the final report must follow the Step 5 template: layered signal tables → contradiction analysis → probability scenarios → signal consistency assessment. Do not substitute prose for structured reporting.

## Workflow

### Step 1: Understand the question

Decompose the user's question into:
- **Core variable**: What event or trend?
- **Time window**: Is the user asking about 3 months, 1 year, or 5 years?
- **Priceability**: Is there real money being traded on this outcome?

### Step 2: Select signals

Based on question type, select from the signal menu below. **Don't use just one category — cover at least 3.**

#### Geopolitical conflict / War risk
- Polymarket: Search for related event contracts (ceasefire, invasion, regime change, declaration of war)
- Kalshi: Search for related binary contracts
- Safe-haven assets: Gold (xauusd), silver (xagusd), Swiss franc (usdchf)
- Conflict proxies: Crude oil (cl.c), natural gas (ng.c), wheat (zw.c), defense ETF (ita.us), defense stocks
- Risk ratios: Copper/Gold ratio (risk-off indicator), Gold/Silver ratio
- CFTC COT: Institutional positioning changes in crude/gold/wheat (which direction is smart money betting)
- BIS: Central bank policy rate trends in relevant countries
- Web search: VIX, MOVE index, sovereign CDS, war risk premiums, BDI freight rates
- Currencies: Currency pairs of relevant countries (e.g. usdrub, usdcny)
- Country ETFs: Asset flows in relevant countries (e.g. fxi.us, ewy.us)

#### Economic recession / Macro cycle
- Treasury: Yield curve shape (10Y-2Y spread, 10Y-3M spread), real rates, breakeven inflation
- Stooq: SPY, copper (hg.c), crude oil, BDI freight rate trends
- Risk ratios: Copper/Gold ratio
- CFTC COT: Speculative net positions in copper/crude (is managed money bullish or bearish)
- BIS: Credit-to-GDP gap (credit overheating = late cycle), policy rate directions
- World Bank: GDP growth rate historical trends, cross-country comparisons
- Deribit: BTC futures basis (risk appetite proxy)
- CoinGecko: Crypto total market cap + BTC dominance (risk appetite proxy)
- Polymarket: Recession-related contracts, central bank rate path
- Currencies: DXY/dollar strength, emerging market currencies
- Web search: High-yield bond spread (HY OAS), TED spread, MOVE index

#### Industry cycle / Bubble assessment
- Stooq: Industry leader stock trends, sector ETFs
- Find the industry's "single-purpose commodity" (e.g. GPU rental price → AI, rebar → construction)
- Upstream equipment maker orders/stock price (e.g. ASML → semiconductors)
- Leader company valuation discount (e.g. TSMC vs peers → Taiwan Strait risk pricing)
- EDGAR: Industry leader insider trading cadence (Form 4) — concentrated selling = bearish signal
- CFTC COT: Institutional positioning changes in related commodities
- CoinGecko: For crypto industry, look at BTC/ETH/altcoin market cap distribution
- Web search: VC funding concentration, leveraged ETF concentration
- Deribit: Implied volatility of related crypto assets

#### Asset pricing / Whether to buy
- Stooq: Target asset price trend (daily/weekly/monthly)
- Relative price changes of correlated assets (divergence between two commodities = structural signal)
- Treasury: Risk-free rate as valuation anchor
- YFinance: Options chain (IV, put/call ratio, max pain, Greeks, implied move)
- EDGAR: Insider selling cadence (heavy Form 4 selling = insiders bearish)
- CFTC COT: Speculative vs commercial net position divergence for commodity assets
- CoinGecko: For crypto assets, check market cap, ATH/ATL distance, 24h volatility
- Deribit: Crypto options chain (implied volatility = market's expected range)
- Polymarket/Kalshi: Probability pricing of related events
- Web search: Corporate bond issuance volume, analyst rating distribution

#### Stock/Options analysis / Crash probability
- YFinance: Options chain → ATM IV (expected volatility), IV skew (upside/downside fear asymmetry), put/call ratio (bull/bear sentiment), max pain (market maker profit zone), implied move (expected price range), Greeks (delta ≈ ITM probability)
- Stooq: Underlying historical price → realized volatility (compare vs implied volatility to judge options premium)
- Kalshi: SPY/NASDAQ price range markets → direct probability pricing
- CFTC COT: S&P 500/VIX futures positioning → institutional direction
- Defensive rotation: XLY (cyclical) vs XLP (defensive) vs XLU (utilities) relative performance → market defensiveness
- Treasury: Yield curve shape → recession signal
- Web search: VIX level, margin debt level, leveraged ETF concentration

**Available trading symbols directory:** See [references/symbols.md](references/symbols.md)
**Provider API reference:** See [references/providers.md](references/providers.md)

### Step 3: Fetch data

Use digital-oracle's Python providers to fetch structured data, calling all sources in parallel with `gather()` (including web search):

```python
from digital_oracle import (
    PolymarketProvider, PolymarketEventQuery,
    KalshiProvider, KalshiMarketQuery,
    StooqProvider, PriceHistoryQuery,
    DeribitProvider, DeribitFuturesCurveQuery,
    USTreasuryProvider, YieldCurveQuery,
    WebSearchProvider,
    CftcCotProvider, CftcCotQuery,
    CoinGeckoProvider, CoinGeckoPriceQuery,
    EdgarProvider, EdgarInsiderQuery,
    BisProvider, BisRateQuery,
    WorldBankProvider, WorldBankQuery,
    YFinanceProvider, OptionsChainQuery,  # requires uv pip install yfinance
    gather,
)

pm = PolymarketProvider()
kalshi = KalshiProvider()
stooq = StooqProvider()
deribit = DeribitProvider()
treasury = USTreasuryProvider()
web = WebSearchProvider()
cftc = CftcCotProvider()
coingecko = CoinGeckoProvider()
edgar = EdgarProvider(user_email="eyelidstl@gmail.com")  # SEC requires email in User-Agent, otherwise 403
bis = BisProvider()
wb = WorldBankProvider()
yf = YFinanceProvider()  # requires uv pip install yfinance

result = gather({
    "pm_events": lambda: pm.list_events(PolymarketEventQuery(slug_contains="...", limit=10)),
    "yield_curve": lambda: treasury.latest_yield_curve(),
    "gold": lambda: stooq.get_history(PriceHistoryQuery(symbol="xauusd", limit=30)),
    # Institutional positioning
    "gold_cot": lambda: cftc.list_reports(CftcCotQuery(commodity_name="GOLD", limit=4)),
    # Crypto market sentiment
    "crypto": lambda: coingecko.get_prices(CoinGeckoPriceQuery(coin_ids=("bitcoin", "ethereum"))),
    # Insider trades
    "insider": lambda: edgar.get_insider_transactions(EdgarInsiderQuery(ticker="AAPL", limit=10)),
    # Central bank policy rates
    "rates": lambda: bis.get_policy_rates(BisRateQuery(countries=("US", "CN"), start_year=2023)),
    # GDP data
    "gdp": lambda: wb.get_indicator(WorldBankQuery(indicator="NY.GDP.MKTP.CD", countries=("US", "CN"))),
    # Options chain (with Greeks)
    "spy_options": lambda: yf.get_chain(OptionsChainQuery(ticker="SPY", expiration="2026-04-17")),
    # Web search runs in parallel with structured providers
    "vix": lambda: web.search("VIX index current level"),
    "hy_spread": lambda: web.search("US high yield bond spread OAS"),
})

# Partial failures don't affect other results
curve = result.get("yield_curve")
vix_info = result.get_or("vix", None)  # WebSearchResult — render with .text()

# Options data usage
chain = result.get_or("spy_options", None)
if chain:
    print(f"ATM IV: {chain.atm_iv:.1%}, Implied move: {chain.implied_move():.1%}")
    print(f"Put/Call OI ratio: {chain.put_call_oi_ratio:.2f}")
    print(f"Max pain: {chain.max_pain()}")
```

**All 12 Providers:**

| Provider | Data Type | Purpose | Dependency |
|----------|-----------|---------|------------|
| PolymarketProvider | Prediction market contracts | Event probability pricing | stdlib |
| KalshiProvider | Binary contracts | US regulated event contracts | stdlib |
| StooqProvider | Price history | Stocks/ETFs/FX/Commodities | stdlib |
| DeribitProvider | Crypto derivatives | Futures term structure, options IV | stdlib |
| USTreasuryProvider | Treasury yields | Yield curves, inflation expectations | stdlib |
| WebSearchProvider | Web search | VIX/MOVE/CDS supplementary data | stdlib |
| CftcCotProvider | Futures positioning | Institutional direction (smart money) | stdlib |
| CoinGeckoProvider | Crypto spot | BTC/ETH price, market cap, dominance | stdlib |
| EdgarProvider | SEC filings | Insider trades Form 4, filing search | stdlib |
| BisProvider | Central bank data | Policy rates, credit-to-GDP gap | stdlib |
| WorldBankProvider | Development indicators | GDP, population, trade, macro data | stdlib |
| **YFinanceProvider** | **US options chains** | **IV, Greeks, put/call ratio, max pain** | **yfinance** |

> 11 out of 12 providers have zero external dependencies. YFinanceProvider requires `pip install yfinance`.

**WebSearchProvider usage:**
- `web.search("query")` → returns `WebSearchResult` (search summary) — render with `.text()`
- `web.fetch_page("url")` → returns `WebPageContent` (page body extraction)
- Search engine is DuckDuckGo, zero API keys needed

**Data not available on Stooq — use web search instead:** VIX, MOVE, CDS spreads, TTF natural gas, BDI freight rates, war risk premiums, IMF forecasts — these need to be fetched from financial web pages. They are still trading data and comply with the methodology.

### Step 4: Contradiction analysis

This is the key to report quality. Don't just summarize data — find contradictions:

- **Are different markets saying different things?** e.g. gold says "disaster" but equities say "fine" — explain why both can be right simultaneously
- **Is there divergence within the same asset class?** e.g. copper up but iron ore down — that divergence itself is a signal
- **Do short-term and long-term signals contradict?** e.g. defense stocks price a 10-year trend but prediction markets only look 1 year ahead — not a contradiction, different time frames
- **Does market pricing contradict intuition?** e.g. CNY strengthening while Taiwan Strait risk rises — smart money doesn't believe in near-term conflict

**Principles when signals diverge:** Don't "vote by majority" — instead:

1. **Check the time dimension first** — different signals price different future windows:
   - Short-term (3-12mo): Prediction market contracts, VIX/MOVE, price reaction patterns, executive selling
   - Medium-term (1-3yr): Leader revenue consensus, CapEx plans, VC concentration, leverage concentration
   - Long-term (3-10yr): Equipment maker orders, irreversible capital allocation, ultra-long infrastructure investment
   - Short-term bearish + long-term bullish ≠ contradiction, = S-curve inflection
2. **Look for "two things happening at once"** — old economy Japanification + new economy boom can coexist in the same economy
3. **"Direction right but timing wrong"** — long-term signals bullish but short-term overheated → conclusion isn't "buy/don't buy" but "wait for a pullback"

### Step 5: Output report

**Must follow this structure.** You can adjust the number of layers and wording, but the four main sections (data summary, synthesis, probability estimates, signal consistency assessment) cannot be omitted or merged into prose paragraphs:

```markdown
# [Question Title]: Multi-Signal Synthesis

## Data Summary

### Layer 1: [Most direct signal source]
| Signal | Data | What it's saying |
|--------|------|-----------------|
(table, one signal per row, third column is reasoning)

### Layer 2: [Secondary signal source]
(same format)

### Layer N: ...
(as needed, typically 3-5 layers)

## Synthesis

### N key contradictions converging:
**Contradiction 1: [A says X, B says Y]**
- Data points...
- Interpretation: why both can be right simultaneously

**Contradiction 2: ...**

## Probability Estimates
| Scenario | Probability | Basis |
|----------|-------------|-------|

### Most likely path: [one-sentence summary]
**Core logic chain:** (2-3 paragraphs, reasoning from data to conclusion)

## Signal Consistency Assessment
| Signal Type | Direction | Confidence |
|-------------|-----------|------------|
(assess reliability of each signal)

**Conclusion: [one-sentence wrap-up]**

---
*Data sources: [list all structured and web data sources]*
*Fetched at: [date]*
```

## Notes

- Polymarket `slug_contains` search is fuzzy — filter results by title keywords after fetching
- Stooq futures symbols use `.c` suffix (e.g. `hg.c`, `ng.c`, `zw.c`, `cl.c`), not `.f`
- Stooq has limited European stock coverage (e.g. Rheinmetall unavailable) — supplement with web search
- Prediction market contracts vary in liquidity — contracts with volume < $100K should be discounted
- Different signals update at different frequencies: prediction markets real-time, Stooq daily delayed, Treasury weekly
- CFTC COT updates Tuesday, published Friday. commodity_name uses uppercase ("GOLD", "CRUDE OIL", "S&P 500")
- CoinGecko free API has rate limits (~10-30 req/min) — don't pack too many CoinGecko calls in gather
- EDGAR requires `EdgarProvider(user_email="you@example.com")` — SEC requires email in User-Agent, otherwise 403. First call parses ticker→CIK mapping, slightly slow
- BIS data updates infrequently (monthly/quarterly) — suitable for long-term trends, not short-term trading
- World Bank GDP data typically lags 1-2 years — latest year may return `None`
- YFinance requires `uv pip install yfinance` (auto-installs pandas). After-hours IV may be inaccurate (bid/ask = 0) — use during market hours
- YFinance `get_chain()` auto-computes Black-Scholes Greeks (pure stdlib `math.erf`, no scipy needed)
- Absolute value of put delta ≈ probability of that strike being ITM at expiration (rough estimate)
- Put/Call ratio > 1.5 is typically bearish, but as a contrarian indicator, extreme values (> 3) may signal a bottom
- Max pain is the strike price maximizing market maker profit — actual expiration price often converges toward max pain
- When reporting dollar amounts, use `USD` instead of `$` to avoid markdown renderers interpreting `$...$` as LaTeX
