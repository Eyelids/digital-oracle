# Provider API 速查

所有 provider 在 `predict-by-emh/` 项目目录下运行。零外部依赖。

```python
from predict_by_emh import (
    PolymarketProvider, PolymarketEventQuery,
    KalshiProvider, KalshiMarketQuery,
    StooqProvider, PriceHistoryQuery,
    DeribitProvider, DeribitFuturesCurveQuery, DeribitOptionChainQuery,
    USTreasuryProvider, YieldCurveQuery, ExchangeRateQuery,
)
```

## PolymarketProvider

预测市场。搜索事件合约，获取概率定价和 orderbook。

```python
p = PolymarketProvider()

# 搜索事件（slug_contains 很模糊，搜到后要按标题关键词二次过滤）
events = p.list_events(PolymarketEventQuery(
    slug_contains="russia",    # 模糊搜索
    limit=20,                  # 返回条数
    active=True,               # 仅活跃事件
    closed=False,              # 排除已关闭
))
# 返回 list[PolymarketEvent]
# event.title, event.slug, event.volume, event.markets
# market.question, market.yes_probability, market.outcomes

# 按 slug 精确获取单个事件
event = p.get_event("russia-x-ukraine-ceasefire-by-march-31-2026")
# 返回 PolymarketEvent | None

# 获取 orderbook（需要 token_id，从 market.outcomes[i].token_id 获取）
book = p.get_order_book(token_id="...")
# book.best_bid, book.best_ask, book.spread
```

## KalshiProvider

美国监管的事件合约市场。按 series/event ticker 组织。

```python
k = KalshiProvider()

# 列出市场（按 series_ticker 过滤）
markets = k.list_markets(KalshiMarketQuery(series_ticker="KXFED", limit=10))
# 返回 list[KalshiMarket]
# market.ticker, market.title, market.yes_probability, market.volume

# 单个市场详情
market = k.get_market("KXFED-27APR-T4.25")

# 事件（包含多个阶梯式市场）
event = k.get_event("KXFED-27APR")
# event.markets -> 该事件下所有市场

# Orderbook
book = k.get_order_book("KXFED-27APR-T4.25", depth=10)
# book.best_yes_ask, book.best_no_ask
```

## StooqProvider

全球价格历史。股票、ETF、外汇、商品、指数。

```python
s = StooqProvider()

hist = s.get_history(PriceHistoryQuery(
    symbol="xauusd",     # 见 symbols.md
    interval="m",        # d=日线 w=周线 m=月线
    limit=12,            # 最近 N 根 bar
))
# 返回 PriceHistory
# hist.bars -> list[PriceBar]
# bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume
# hist.latest -> 最新 bar
# hist.earliest -> 最早 bar
```

**符号命名规则：**
- 美股: `spy.us`, `lmt.us`, `ccj.us`
- 外汇: `eurusd`, `usdjpy`, `usdchf`
- 商品期货: `hg.c`, `ng.c`, `zw.c`, `cl.c`
- 贵金属: `xauusd`, `xagusd`
- 英股: `ba.uk`

## DeribitProvider

加密衍生品。期货 term structure、期权链、orderbook。

```python
d = DeribitProvider()

# 期货 term structure（contango/backwardation = 市场情绪）
ts = d.get_futures_term_structure(DeribitFuturesCurveQuery(currency="BTC"))
# ts.points -> list[DeribitFutureTermPoint]
# point.instrument_name, point.mark_price, point.basis_vs_perpetual, point.annualized_basis_vs_perpetual
# ts.perpetual() -> 永续合约数据

# 期权链（隐含波动率 = 市场预期波动范围）
chain = d.get_option_chain(DeribitOptionChainQuery(
    currency="BTC",
    expiration_label="27MAR26",  # 可选，不填取最近到期
))
# chain.strikes, chain.underlying_price, chain.atm_strike()

# Orderbook
book = d.get_order_book("BTC-PERPETUAL", depth=5)
# book.best_bid, book.best_ask, book.spread, book.mark_price, book.index_price
```

## USTreasuryProvider

美国国债收益率曲线 + 财政部汇率数据。

```python
t = USTreasuryProvider()

# 收益率曲线
snapshots = t.list_yield_curve(YieldCurveQuery(
    year=2026,
    curve_kind="nominal",   # nominal | real | bill | long_term
))
# 返回 list[YieldCurveSnapshot]，按日期排列
# snap.date, snap.points -> list[YieldPoint]
# point.tenor ("1M", "3M", "2Y", "10Y", "30Y"), point.value (百分比)

# 快捷方法
snap = t.latest_yield_curve(YieldCurveQuery(year=2026, curve_kind="nominal"))
y10 = snap.yield_for("10Y")  # -> float | None
spread = snap.spread("10Y", "2Y")  # -> float | None (百分比差)

# 盈亏平衡通胀 = nominal - real
nominal = t.latest_yield_curve(YieldCurveQuery(year=2026, curve_kind="nominal"))
real = t.latest_yield_curve(YieldCurveQuery(year=2026, curve_kind="real"))
breakeven_10y = nominal.yield_for("10Y") - real.yield_for("10Y")

# 汇率
rates = t.list_exchange_rates(ExchangeRateQuery(country=("China", "Japan")))
# 返回 list[ExchangeRateRecord]
# record.country, record.currency, record.exchange_rate
```
