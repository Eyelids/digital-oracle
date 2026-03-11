---
name: predict-by-emh
description: "Answer prediction questions using market trading data, not opinions. Use when the user asks probability questions about geopolitics, economics, markets, industries, or any topic where real money is being traded on the outcome. Examples: 'What's the probability of WW3?', 'Will there be a recession?', 'Is AI in a bubble?', 'When will the Russia-Ukraine war end?', 'Is it a good time to buy gold?'. The skill reads prices from prediction markets, commodities, equities, derivatives, yield curves, and currencies, then cross-validates multiple signals to produce a structured probability report."
---

# predict-by-emh

> 市场是有效的，价格包含了所有公开信息。读价格 = 读市场共识。

## 方法论

**只用市场交易数据回答问题，不用新闻、观点、统计报告做因果。** 如果某个信息是真的，一定已经被某个市场定价了。

四条铁律：

1. **只看交易数据** — 价格、成交量、持仓量、利差、保费。不引用分析师观点。
2. **从价格到判断需要显式推理** — 说清楚"这个价格为什么能回答这个问题"。
3. **多信号交叉验证** — 单一信号不出结论。至少 3 个独立维度。
4. **标注每个信号的时间维度** — 期权定价 3 个月，设备订单定价 3 年，不能混在一起投票。

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
- Web search: VIX、MOVE index、主权CDS、战争险保费、BDI运价
- 货币: 相关国家货币对（如 usdrub, usdcny）
- 国家ETF: 相关国家资产流向（如 fxi.us, ewy.us）

#### 经济衰退 / 宏观周期
- Treasury: 收益率曲线形态（10Y-2Y利差、10Y-3M利差）、实际利率、盈亏平衡通胀
- Stooq: SPY、铜(hg.c)、原油、BDI运价走势
- 风险比率: Copper/Gold ratio
- Deribit: BTC期货基差（risk appetite proxy）
- Polymarket: 衰退相关合约、央行利率路径
- 货币: DXY/美元强弱、新兴市场货币
- Web search: 高收益债利差(HY OAS)、TED spread、MOVE index

#### 行业周期 / 泡沫判断
- Stooq: 行业龙头股价走势、行业ETF
- 找到该行业的"单一用途商品"（如GPU租赁价→AI、螺纹钢→建筑）
- 上游设备商订单/股价（如ASML→半导体）
- 龙头公司估值折价（如台积电 vs 同行 → 台海风险定价）
- Web search: 风投融资集中度、杠杆ETF集中度
- Deribit: 相关加密资产的期权隐含波动率

#### 资产定价 / 是否值得买入
- Stooq: 目标资产价格走势（日线/周线/月线）
- 相关资产的相对价格变化（两种商品价差分化 = 结构性信号）
- Treasury: 无风险利率作为估值锚
- Deribit: 期权链（隐含波动率 = 市场预期的波动范围）
- Polymarket/Kalshi: 相关事件的概率定价
- Web search: 内部人减持节奏、企业发债规模

**详细的元信号参考：** 见 [references/signals.md](references/signals.md)
**可用交易符号目录：** 见 [references/symbols.md](references/symbols.md)
**Provider API 速查：** 见 [references/providers.md](references/providers.md)

### Step 3: 拉取数据

用 predict-by-emh 的 Python provider 拉取结构化数据，用 `gather()` 并行调用所有数据源（包括 web search）：

```python
from predict_by_emh import (
    PolymarketProvider, PolymarketEventQuery,
    KalshiProvider, KalshiMarketQuery,
    StooqProvider, PriceHistoryQuery,
    DeribitProvider, DeribitFuturesCurveQuery,
    USTreasuryProvider, YieldCurveQuery,
    WebSearchProvider,
    gather,
)

pm = PolymarketProvider()
kalshi = KalshiProvider()
stooq = StooqProvider()
deribit = DeribitProvider()
treasury = USTreasuryProvider()
web = WebSearchProvider()

result = gather({
    "pm_events": lambda: pm.list_events(PolymarketEventQuery(slug_contains="...", limit=10)),
    "yield_curve": lambda: treasury.latest_yield_curve(),
    "gold": lambda: stooq.get_history(PriceHistoryQuery(symbol="xauusd", limit=30)),
    # web search 与结构化 provider 平行执行
    "vix": lambda: web.search("VIX index current level"),
    "hy_spread": lambda: web.search("US high yield bond spread OAS"),
})

# 部分数据源失败不影响其他结果
curve = result.get("yield_curve")
vix_info = result.get_or("vix", None)  # WebSearchResult，用 .text() 渲染
```

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

**信号分裂时的处理原则：** 不是"投票取多数"，而是看每个信号定价的时间窗口。短期悲观+长期乐观 = S曲线正在弯折，不是矛盾。答案很可能是"两件不同的事在同时发生"。

### Step 5: 输出报告

使用以下固定结构：

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
