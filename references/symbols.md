# Stooq 交易符号目录

通过 StooqProvider 验证可用的符号。使用 `get_history(PriceHistoryQuery(symbol=..., interval='d'|'w'|'m', limit=N))` 拉取。

## 贵金属

| 符号 | 标的 | 信号含义 |
|------|------|---------|
| `xauusd` | 黄金/美元 | 核心避险资产，尾部风险定价 |
| `xagusd` | 白银/美元 | 避险+工业双重需求（军工/光伏用银） |

**常用比率：**
- Gold/Silver ratio = xauusd / xagusd — 上升=纯避险主导，下降=工业需求也在涨（或投机狂热）
- 历史中位 ~70，极端避险时 >100，投机狂热时 <50

## 能源

| 符号 | 标的 | 信号含义 |
|------|------|---------|
| `cl.c` | WTI原油期货 | 供应中断/地缘冲突代理 |
| `ng.c` | 美国天然气期货 | 北美能源供需 |

**Stooq 拿不到，需 web search：**
- TTF (欧洲天然气) — 搜 "TTF natural gas price"
- Brent crude — 搜 "brent crude oil price"

## 粮食

| 符号 | 标的 | 信号含义 |
|------|------|---------|
| `zw.c` | 小麦期货 | 黑海粮食通道/战争持续性 |
| `zc.c` | 玉米期货 | 全球粮食供需 |
| `zs.c` | 大豆期货 | 南美/中国贸易 |

## 工业金属

| 符号 | 标的 | 信号含义 |
|------|------|---------|
| `hg.c` | 铜期货 | 全球工业活动晴雨表 |

**常用比率：**
- Copper/Gold ratio = hg.c / xauusd * 1000 — 下降=risk-off（工业需求弱于避险需求），上升=risk-on

## 美国防务股 & ETF

| 符号 | 标的 | 信号含义 |
|------|------|---------|
| `lmt.us` | Lockheed Martin | 美国最大防务承包商 |
| `rtx.us` | Raytheon/RTX | 导弹/防空系统 |
| `gd.us` | General Dynamics | 舰艇/陆战系统 |
| `noc.us` | Northrop Grumman | 隐身/太空 |
| `ita.us` | iShares US Aerospace & Defense ETF | 美国防务板块整体 |
| `xar.us` | SPDR S&P Aerospace & Defense ETF | 等权防务ETF |
| `ppa.us` | Invesco Aerospace & Defense ETF | 防务ETF替代 |

**Stooq 拿不到的欧洲防务股，需 web search：**
- Rheinmetall (RHM.DE) — 欧洲重新武装旗舰
- BAE Systems (BA.L) — 英国防务龙头（Stooq 有 `ba.uk`）
- Thales, Leonardo, Saab — 需 web search

## 铀矿 & 核能

| 符号 | 标的 | 信号含义 |
|------|------|---------|
| `ccj.us` | Cameco | 全球最大铀矿商 |
| `uec.us` | Uranium Energy Corp | 美国铀矿 |

铀现货价需 web search — 搜 "uranium spot price"

## 美国大盘 & 波动率

| 符号 | 标的 | 信号含义 |
|------|------|---------|
| `spy.us` | S&P 500 ETF | 美国股市整体 |
| `qqq.us` | Nasdaq 100 ETF | 科技股整体 |
| `vixy.us` | ProShares VIX Short-Term ETF | VIX代理（Stooq拿不到^VIX本身） |

VIX/MOVE 精确值需 web search — 搜 "VIX index current" / "MOVE index current"

## 货币对

| 符号 | 标的 | 信号含义 |
|------|------|---------|
| `eurusd` | 欧元/美元 | 欧美经济相对强弱 |
| `usdjpy` | 美元/日元 | 日元是传统避险货币，但也受利差驱动 |
| `usdchf` | 美元/瑞郎 | 瑞郎是最纯的避险货币，下降=避险资金流入 |
| `usdcny` | 美元/人民币 | 中国资本流向，下降=人民币走强=资本流入 |
| `usdrub` | 美元/卢布 | 俄罗斯制裁压力/能源收入 |
| `gbpusd` | 英镑/美元 | 英国经济 |

## 国家 & 地区 ETF

| 符号 | 标的 | 信号含义 |
|------|------|---------|
| `fxi.us` | iShares China Large-Cap ETF | 外资对中国资产的风险定价 |
| `ewy.us` | iShares MSCI South Korea ETF | 韩国/朝鲜半岛风险 |
| `ewz.us` | iShares MSCI Brazil ETF | 巴西/新兴市场 |
| `ewa.us` | iShares MSCI Australia ETF | 大宗商品国 |

## 需要 Web Search 的关键数据

以下数据 Stooq 无法提供，但对分析至关重要，需通过 web search 获取：

| 数据 | 搜索关键词 | 信号含义 |
|------|-----------|---------|
| VIX | "VIX index current" | 股市隐含波动率，短期恐慌度 |
| MOVE Index | "MOVE index bond volatility" | 债市隐含波动率 |
| 主权 CDS | "[国家] sovereign CDS 5 year spread" | 国家违约/战争风险直接定价 |
| TTF 天然气 | "TTF European natural gas price" | 欧洲能源安全 |
| BDI 运价 | "Baltic Dry Index current" | 全球航运活动 |
| 战争险保费 | "war risk insurance premium shipping [地区]" | 保险市场对冲突区的直接定价 |
| 高收益债利差 | "US high yield OAS spread" | 信用风险溢价 |
