---
name: digital-oracle
description: "Answer prediction questions using market trading data, not opinions. Use when the user asks probability questions about geopolitics, economics, markets, industries, or any topic where real money is being traded on the outcome. Examples: 'What's the probability of WW3?', 'Will there be a recession?', 'Is AI in a bubble?', 'When will the Russia-Ukraine war end?', 'Is it a good time to buy gold?', 'Will SPY drop 5% this month?', 'Is NVDA options premium overpriced?'. The skill reads prices from prediction markets, commodities, equities, options chains, derivatives, yield curves, and currencies, then cross-validates multiple signals to produce a structured probability report."
metadata: { "openclaw": { "emoji": "📈", "requires": { "bins": ["uv"] } } }
---

# digital-oracle

> 市场是有效的，价格包含了所有公开信息。读价格 = 读市场共识。

## 方法论

**只用市场交易数据回答问题，不用新闻、观点、统计报告做因果。** 如果某个信息是真的，一定已经被某个市场定价了。

四条铁律：

1. **只看交易数据** — 价格、成交量、持仓量、利差、保费。不引用分析师观点。
2. **从价格到判断需要显式推理** — 说清楚"这个价格为什么能回答这个问题"。
3. **多信号交叉验证** — 单一信号不出结论。至少 3 个独立维度。
4. **标注每个信号的时间维度** — 期权定价 3 个月，设备订单定价 3 年，不能混在一起投票。
5. **结构化输出** — 最终报告必须按 Step 5 的模板输出：分层信号表格 → 矛盾推理 → 概率场景 → 信号一致性评估。不要用散文体叙述代替结构化报告。

## 工作流程

### Step 1: 理解问题

把用户的问题拆解为：
- **核心变量**：什么事件/趋势？
- **时间窗口**：用户关心的是 3 个月、1 年、还是 5 年？
- **可定价性**：有没有真金白银在交易这个结果？

### Step 2: 选择信号

根据问题类型，从下面的信号菜单中选择。**不要只用一个类别，至少覆盖 3 个。**

#### 地缘冲突 / 战争风险
- Polymarket: 搜索相关事件合约（停火、入侵、政权更迭、宣战）
- Kalshi: 搜索相关二元合约
- 避险资产: 黄金(xauusd)、白银(xagusd)、瑞郎(usdchf)
- 冲突代理: 原油(cl.c)、天然气(ng.c)、小麦(zw.c)、防务ETF(ita.us)、防务个股
- 风险比率: Copper/Gold ratio (risk-off指标)、Gold/Silver ratio
- CFTC COT: 原油/黄金/小麦的机构持仓变化（smart money 在押注什么方向）
- BIS: 相关国家央行政策利率变化趋势
- Web search: VIX、MOVE index、主权CDS、战争险保费、BDI运价
- 货币: 相关国家货币对（如 usdrub, usdcny）
- 国家ETF: 相关国家资产流向（如 fxi.us, ewy.us）

#### 经济衰退 / 宏观周期
- Treasury: 收益率曲线形态（10Y-2Y利差、10Y-3M利差）、实际利率、盈亏平衡通胀
- Stooq: SPY、铜(hg.c)、原油、BDI运价走势
- 风险比率: Copper/Gold ratio
- CFTC COT: 铜/原油的投机净仓位（managed money 看涨还是看跌）
- BIS: 信贷/GDP 缺口（信用过热 = 周期尾声）、各国政策利率走向
- World Bank: GDP 增长率历史趋势、横向国别对比
- Deribit: BTC期货基差（risk appetite proxy）
- CoinGecko: 加密总市值 + BTC dominance（风险偏好代理）
- Polymarket: 衰退相关合约、央行利率路径
- 货币: DXY/美元强弱、新兴市场货币
- Web search: 高收益债利差(HY OAS)、TED spread、MOVE index

#### 行业周期 / 泡沫判断
- Stooq: 行业龙头股价走势、行业ETF
- 找到该行业的"单一用途商品"（如GPU租赁价→AI、螺纹钢→建筑）
- 上游设备商订单/股价（如ASML→半导体）
- 龙头公司估值折价（如台积电 vs 同行 → 台海风险定价）
- EDGAR: 行业龙头内部人买卖节奏（Form 4），集中减持 = 看空信号
- CFTC COT: 相关商品的机构持仓变化
- CoinGecko: 加密行业看 BTC/ETH/altcoin 市值分布
- Web search: 风投融资集中度、杠杆ETF集中度
- Deribit: 相关加密资产的期权隐含波动率

#### 资产定价 / 是否值得买入
- Stooq: 目标资产价格走势（日线/周线/月线）
- 相关资产的相对价格变化（两种商品价差分化 = 结构性信号）
- Treasury: 无风险利率作为估值锚
- YFinance: 期权链（IV、put/call ratio、max pain、Greeks、implied move）
- EDGAR: 内部人减持节奏（大量 Form 4 卖出 = 内部人看空）
- CFTC COT: 商品类资产看投机/商业净仓位分歧
- CoinGecko: 加密资产看市值、ATH/ATL 距离、24h 波动
- Deribit: 加密期权链（隐含波动率 = 市场预期的波动范围）
- Polymarket/Kalshi: 相关事件的概率定价
- Web search: 企业发债规模、分析师评级分布

#### 股票/期权分析 / 崩盘概率
- YFinance: 期权链 → ATM IV（市场预期波动）、IV skew（上下行恐惧不对称）、put/call ratio（多空情绪）、max pain（做市商利益区）、implied move（市场预期涨跌幅）、Greeks（delta ≈ ITM概率）
- Stooq: 标的历史价格 → 实际波动率（对比隐含波动率判断期权溢价）
- Kalshi: SPY/NASDAQ 价格区间市场 → 直接概率定价
- CFTC COT: S&P 500/VIX 期货持仓 → 机构方向
- 防御轮换: XLY(周期) vs XLP(防御) vs XLU(公用) 相对表现 → 市场防御心态
- Treasury: 收益率曲线形态 → 衰退信号
- Web search: VIX 水平、margin debt 水平、杠杆ETF 集中度

**可用交易符号目录：** 见 [references/symbols.md](references/symbols.md)
**Provider API 速查：** 见 [references/providers.md](references/providers.md)

### Step 3: 拉取数据

用 digital-oracle 的 Python provider 拉取结构化数据，用 `gather()` 并行调用所有数据源（包括 web search）：

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
    YFinanceProvider, OptionsChainQuery,  # 需要 uv pip install yfinance
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
edgar = EdgarProvider(user_email="eyelidstl@gmail.com")  # SEC要求带邮箱，否则403
bis = BisProvider()
wb = WorldBankProvider()
yf = YFinanceProvider()  # 需要 uv pip install yfinance

result = gather({
    "pm_events": lambda: pm.list_events(PolymarketEventQuery(slug_contains="...", limit=10)),
    "yield_curve": lambda: treasury.latest_yield_curve(),
    "gold": lambda: stooq.get_history(PriceHistoryQuery(symbol="xauusd", limit=30)),
    # 机构持仓
    "gold_cot": lambda: cftc.list_reports(CftcCotQuery(commodity_name="GOLD", limit=4)),
    # 加密市场情绪
    "crypto": lambda: coingecko.get_prices(CoinGeckoPriceQuery(coin_ids=("bitcoin", "ethereum"))),
    # 内部人交易
    "insider": lambda: edgar.get_insider_transactions(EdgarInsiderQuery(ticker="AAPL", limit=10)),
    # 央行政策利率
    "rates": lambda: bis.get_policy_rates(BisRateQuery(countries=("US", "CN"), start_year=2023)),
    # GDP 数据
    "gdp": lambda: wb.get_indicator(WorldBankQuery(indicator="NY.GDP.MKTP.CD", countries=("US", "CN"))),
    # 期权链（含 Greeks）
    "spy_options": lambda: yf.get_chain(OptionsChainQuery(ticker="SPY", expiration="2026-04-17")),
    # web search 与结构化 provider 平行执行
    "vix": lambda: web.search("VIX index current level"),
    "hy_spread": lambda: web.search("US high yield bond spread OAS"),
})

# 部分数据源失败不影响其他结果
curve = result.get("yield_curve")
vix_info = result.get_or("vix", None)  # WebSearchResult，用 .text() 渲染

# 期权数据使用
chain = result.get_or("spy_options", None)
if chain:
    print(f"ATM IV: {chain.atm_iv:.1%}, Implied move: {chain.implied_move():.1%}")
    print(f"Put/Call OI ratio: {chain.put_call_oi_ratio:.2f}")
    print(f"Max pain: {chain.max_pain()}")
```

**所有 12 个 Provider：**

| Provider | 数据类型 | 用途 | 依赖 |
|----------|---------|------|------|
| PolymarketProvider | 预测市场合约 | 事件概率定价 | stdlib |
| KalshiProvider | 二元合约 | 美国监管事件合约 | stdlib |
| StooqProvider | 价格历史 | 股票/ETF/外汇/商品 | stdlib |
| DeribitProvider | 加密衍生品 | 期货term structure、期权IV | stdlib |
| USTreasuryProvider | 国债收益率 | 利率曲线、通胀预期 | stdlib |
| WebSearchProvider | 网页搜索 | VIX/MOVE/CDS等补充数据 | stdlib |
| CftcCotProvider | 期货持仓 | 机构仓位方向（smart money） | stdlib |
| CoinGeckoProvider | 加密现货 | BTC/ETH价格、市值、dominance | stdlib |
| EdgarProvider | SEC文件 | 内部人交易Form 4、公告检索 | stdlib |
| BisProvider | 央行数据 | 政策利率、信贷/GDP缺口 | stdlib |
| WorldBankProvider | 发展指标 | GDP、人口、贸易等宏观数据 | stdlib |
| **YFinanceProvider** | **US期权链** | **IV、Greeks、put/call ratio、max pain** | **yfinance** |

> 前 11 个 provider 零外部依赖。YFinanceProvider 需要 `pip install yfinance`。

**WebSearchProvider 用法：**
- `web.search("query")` → 返回 `WebSearchResult`（搜索摘要），用 `.text()` 渲染为可读文本
- `web.fetch_page("url")` → 返回 `WebPageContent`（页面正文提取）
- 搜索引擎为 DuckDuckGo，零 API key

**Stooq 拉不到的数据用 web search 补：** VIX、MOVE、CDS利差、TTF天然气、BDI运价、战争险保费、IMF预测等需要从金融网页获取。这些仍然是交易数据，符合方法论。

### Step 4: 矛盾推理

这是报告质量的关键。不是简单汇总数据，而是找矛盾：

- **不同市场在说不同的话吗？** 比如黄金说"灾难"但股市说"还行" — 解释为什么两者可以同时正确
- **同一类资产内部有分化吗？** 比如铜涨铁矿跌 — 这本身就是信号
- **短期信号和长期信号矛盾吗？** 比如防务股定价十年趋势但预测市场只看一年 — 不是矛盾，是不同时间框架
- **市场定价和直觉相反吗？** 比如人民币走强但台海风险在上升 — 说明 smart money 不信短期开战

**信号分裂时的处理原则：** 不是"投票取多数"，而是：

1. **先看时间维度** — 不同信号定价不同的未来窗口：
   - 短期(3-12月)：预测市场合约、VIX/MOVE、价格反应模式、高管减持
   - 中期(1-3年)：龙头营收共识、CapEx计划、风投集中度、杠杆集中度
   - 长期(3-10年)：设备商订单、不可逆资本配置、超长基建投资
   - 短期悲观+长期乐观 ≠ 矛盾，= S曲线正在弯折
2. **看"两件事同时发生"** — 旧经济日本化+新经济活跃可以共存于同一经济体
3. **"方向对但时机不对"** — 长期信号看多但短期过热 → 结论不是"买/不买"而是"等回调"

### Step 5: 输出报告

**必须按以下结构输出。** 你可以调整层数和措辞，但四个主要板块（数据汇总、综合推理、概率估计、信号一致性评估）不能省略，也不要合并成散文段落：

```markdown
# [问题标题]：多信号综合分析

## 数据汇总

### 第一层：[最直接的信号源]
| 信号 | 数据 | 它在说什么 |
|------|------|-----------|
(表格，每行一个信号，第三列是推理)

### 第二层：[次要信号源]
(同上格式)

### 第N层：...
(根据问题需要，通常 3-5 层)

## 综合推理

### N组关键矛盾在交汇：
**矛盾一：[A说X，B说Y]**
- 数据点...
- 解读：为什么两者可以同时正确

**矛盾二：...**

## 概率估计
| 场景 | 概率 | 依据 |
|------|------|------|

### 最可能的路径：[一句话总结]
**核心逻辑链：** (2-3段，从数据推导到结论)

## 信号一致性评估
| 信号类型 | 方向 | 可信度 |
|----------|------|--------|
(评估每个信号的可靠程度)

**结论：[一句话收束]**

---
*数据来源：[列出所有结构化和网页数据源]*
*拉取时间：[日期]*
```

## 注意事项

- Polymarket 的 `slug_contains` 搜索很模糊，搜到的结果要按标题关键词二次过滤
- Stooq 期货符号用 `.c` 后缀（如 `hg.c`, `ng.c`, `zw.c`, `cl.c`），不是 `.f`
- Stooq 欧洲股票覆盖有限（Rheinmetall 拿不到），用 web search 补
- 预测市场合约有流动性差异，交易量 < $100K 的合约可信度要打折
- 不同信号的更新频率不同：预测市场实时，Stooq 日线延迟，Treasury 周级更新
- CFTC COT 每周二更新、周五发布，commodity_name 用大写（"GOLD", "CRUDE OIL", "S&P 500"）
- CoinGecko 免费 API 有频率限制（~10-30 req/min），不要在 gather 里塞太多 CoinGecko 调用
- EDGAR 需要 `EdgarProvider(user_email="you@example.com")`，SEC 要求 User-Agent 含邮箱，否则 403。首次调用会解析 ticker→CIK 映射，稍慢
- BIS 数据更新频率较低（月度/季度），适合判断长期趋势而非短期交易
- World Bank GDP 数据通常滞后 1-2 年，最新年份可能返回 `None`
- YFinance 需要 `uv pip install yfinance`（会自动安装 pandas），盘后数据的 IV 可能不准（bid/ask 为 0），建议盘中使用
- YFinance 的 `get_chain()` 自动计算 Black-Scholes Greeks（纯 stdlib `math.erf`，不需要 scipy）
- Put delta 的绝对值 ≈ 该 strike 到期时 ITM 的概率（粗略估计）
- Put/Call ratio > 1.5 通常是看空信号，但作为逆向指标，极端值（> 3）反而暗示底部
- Max pain 是做市商利益最大化的行权价，实际到期时价格常常向 max pain 收敛
- 输出报告中涉及美元金额时，用 `USD` 或 `美元` 代替 `$` 符号，避免 markdown 渲染器把 `$...$` 当作 LaTeX 公式
