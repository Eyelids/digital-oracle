# predict-by-emh: Data Stack

> 目标：筛出**真正适合本地开箱即用**的数据源。优先级不是“最专业”，而是：
> 1. 尽量无 key
> 2. 接入低摩擦
> 3. 适合本地电脑直接跑
> 4. 对 `predict-by-emh` 的信号提取真正有帮助

---

## 一、评估标准

每个数据源都按这几个维度看：

| 维度 | 含义 |
|------|------|
| `no_key` | 是否真的不用 key 或认证 |
| `local_verified` | 是否已经在本机直接请求验证过 |
| `access_mode` | REST / WebSocket / CSV / wrapper / 抓取 |
| `coverage` | 覆盖哪些资产或宏观数据 |
| `emh_value` | 对我们的方法论是否真的有预测价值 |
| `caveats` | 限频、非官方、接口脆弱、仅研究用途等 |

特别说明：

- **“文档上公开”不等于“适合第一版直接接”**
- **“官方”不等于“接入体验好”**
- **“无 key”不等于“稳定”**

---

## 二、第一梯队：已在本机验证、真正可直接接的无 key 数据源

这些数据源已经在本机通过脚本直接请求验证过，能返回结构化数据。

| provider | no_key | local_verified | access_mode | coverage | emh_value | caveats | 推荐级别 |
|----------|--------|----------------|-------------|----------|-----------|---------|----------|
| `Polymarket` | 是 | 是 | REST + WebSocket | 预测市场、价格、盘口、OI、交易、历史价格 | 非常高，直接概率层 | 速率限制，偏事件驱动 | 高 |
| `Kalshi` | 是 | 是 | REST | 预测市场、宏观/政治/经济事件 | 非常高，和 Polymarket 形成交叉验证 | base URL 和市场结构需要封装一下 | 高 |
| `Deribit` | 是 | 是 | REST + WebSocket | BTC/ETH 期权、期货、orderbook、IV、OI | 非常高，尤其适合 crypto 期权层 | 仅 crypto；需要自己做数据整理 | 高 |
| `CoinGecko` | 是 | 是 | REST | crypto 价格、市值、历史、交易所、稳定币基础数据 | 高，适合作为 crypto 现货底座 | 免费限频较低，需缓存 | 高 |
| `Treasury FiscalData` | 是 | 是 | REST | 美国财政、汇率、部分债务与财政数据 | 中高，宏观骨架很有用 | 不直接提供所有市场行情 | 高 |
| `U.S. Treasury Yield Data` | 是 | 是 | CSV / XML / 网页数据 | 美债收益率曲线、真实收益率、长期利率 | 非常高，宏观/黄金/衰退类问题必备 | 数据格式略老，需要清洗 | 高 |
| `SEC EDGAR` | 是 | 是 | REST / JSON | 公司披露、财报、8-K、Form 4 等 | 高，适合“超预期但下跌”“高管减持”类信号 | 需要合规 `User-Agent` | 高 |
| `Stooq` | 是 | 是 | CSV / wrapper | 全球股票、ETF、指数、债券、外汇、部分宏观 | 高，做本地回测和历史走势很方便 | 不是标准 REST API，偏 CSV 下载 | 高 |
| `CFTC COT` | 是 | 是 | JSON / CSV | 期货/商品/金融合约的持仓结构 | 高，适合商品/利率/情绪 | 周度，不是实时 | 高 |

### 这批源的特点

- **优点**：零 key、可立即跑、本机已验证
- **意义**：已经足够构成第一版“全球可运行”的数据底座
- **适用问题**：
  - 事件概率：`Polymarket` + `Kalshi`
  - Crypto：`CoinGecko` + `Deribit`
  - 宏观：`Treasury` + `FiscalData` + `CFTC`
  - 公司层：`SEC EDGAR`
  - 历史价格和回测：`Stooq`

---

## 三、第二梯队：官方公开、无 key，但接入体验一般

这些源文档明确公开，适合做增强层，但未必是第一版最优先。

| provider | no_key | local_verified | access_mode | coverage | emh_value | caveats | 推荐级别 |
|----------|--------|----------------|-------------|----------|-----------|---------|----------|
| `ECB Data API` | 是 | 部分验证 | REST (SDMX) | 欧元区利率、货币、银行、宏观统计 | 高，适合欧洲宏观和跨国比较 | SDMX 学习成本高，返回格式偏重 | 中高 |
| `Eurostat` | 是 | 是 | REST / JSON-stat / CSV | 欧盟通胀、就业、贸易、生产、人口等 | 高，适合跨国对比 | 数据维度复杂，需要统一解析器 | 中高 |
| `World Bank API` | 是 | 是 | REST | 全球国家级宏观指标、通胀、GDP、人口等 | 中高，适合跨国时序对比 | 更新频率偏慢，不是市场级数据 | 中高 |
| `IMF Data API` | 是 | 文档确认，局部未稳定验证 | REST / SDMX | 国际收支、金融、汇率、IFS 数据 | 高，适合国际比较 | 端点文档复杂，部分请求易超时 | 中 |
| `OECD API` | 是 | 文档确认，局部未稳定验证 | REST / SDMX / CSV | OECD 国家宏观、价格、利率、工业等 | 中高，适合发达经济体比较 | 查询语法不友好，限频较明显 | 中 |
| `BIS API` | 是 | 文档确认，具体查询较挑剔 | REST / SDMX | 汇率、信贷、全球流动性、国际银行统计 | 非常高，适合“全球风险”和信用框架 | API 语法不直观，示例要打磨 | 中 |
| `Bank of England` | 是 | 部分验证 | HTML / CSV / 数据库导出 | 英国利率、货币、银行统计、汇率 | 中，适合英镑/英国利率场景 | 更像数据库导出，不像现代 API | 中 |
| `World Gold Council` | 是 | 页面验证 | 网页 + Excel 下载 | 黄金 ETF 流、持仓、AUM、黄金研究数据 | 高，黄金场景很有用 | 非 API，适合定期拉取，不适合高频 | 中 |
| `AkShare` | 是 | 文档和生态确认 | Python wrapper | 中国市场：A股、指数、北向、融资、期货、债券、宏观 | 非常高，中国场景几乎必备 | 底层很多是抓取，稳定性不如官方 API | 高 |

### 这批源的特点

- **价值很高**
- **接入体验不如第一梯队顺滑**
- 更适合作为：
  - 全球宏观对比层
  - 特定主题增强层
  - 中国市场低门槛入口

---

## 四、第三梯队：近乎无门槛，但严格说不是零 key

这些源免费且好用，但用户需要 1 分钟注册一下。适合做“增强模式”，不应成为第一版的强依赖。

| provider | no_key | access_mode | coverage | emh_value | caveats | 推荐级别 |
|----------|--------|-------------|----------|-----------|---------|----------|
| `FRED` | 否（免费 key） | REST | 美国宏观、利率、通胀、就业、货币、国际比较 | 非常高 | 虽然门槛低，但毕竟要注册 | 高 |
| `Tushare Pro` | 否（免费 token） | REST / Python | A股、指数、北向、融资融券、财务、期货、债券 | 非常高 | 免费层部分接口受限 | 高 |
| `Glassnode` | 否（免费层 key） | REST | 链上成本、MVRV、LTH/STH、矿工、交易所流量 | 非常高 | 高价值指标很多在付费层 | 高 |
| `BLS` | 近似（无 key 可用） | REST | 美国 CPI、PPI、就业、工资 | 高 | 无 key 模式限流更紧 | 中 |
| `Finnhub` | 否（免费 key） | REST | 美股、ETF、新闻、部分基本面 | 中高 | 免费额度有限 | 中 |
| `Alpha Vantage` | 否（免费 key） | REST | 股票、外汇、商品、宏观 | 中 | 限频较严，更多像备用源 | 低中 |

### 为什么它们仍然重要

因为如果允许用户多填 **1-2 个 key**，产品质量会明显提升：

- `FRED`：几乎能把美国宏观骨架补齐
- `Tushare`：几乎能把中国市场骨架补齐
- `Glassnode`：几乎能把 BTC 链上层补齐

这三个是“**付出最少配置，提升最大**”的代表。

---

## 五、不建议第一版依赖的源

这些源可能很强，但不符合“本地开箱即用”的目标。

| provider | 问题 | 为什么不适合第一版 |
|----------|------|--------------------|
| `Bloomberg Terminal` | 成本高、依赖重 | 当前瓶颈不是“没终端”，而是方法论还在打磨 |
| `Wind / Choice / iFinD` | 中国数据强但重 | 更适合专业终端，不适合轻量本地产品 |
| `CDS / 航运险 / AIS 专业数据` | 价值高但太贵 | 适合后期地缘增强模块，不适合第一版 |
| `yfinance` | 虽然无 key，但非官方且不稳定 | 可作研究和备用，不建议做唯一主源 |
| `EIA API` | 需要 key | 可做后续能源模块增强，但不是零 key |

---

## 六、按案例看，哪些公开源最有用

| 问题类型 | 第一版最适合的数据源 |
|----------|----------------------|
| 战争/选举/政策事件概率 | `Polymarket` + `Kalshi` |
| BTC 是否值得买 | `CoinGecko` + `Deribit` + （增强：`Glassnode`） |
| 黄金还能不能买 | `Treasury` + `FiscalData` + `World Gold Council` + `Stooq` |
| AI 泡沫会不会破 | `Stooq` + `SEC EDGAR` + `Polymarket` |
| AI 还能高速迭代多久 | `SEC EDGAR` + `Stooq` + `Polymarket` |
| 中国日本化 / 沪深300 | `AkShare` + `World Bank` + `ECB/Eurostat/OECD` 做跨国比较 |
| 全球宏观对比 | `World Bank` + `IMF` + `OECD` + `ECB` + `Treasury` |

---

## 七、第一版建议接入顺序

### 零 key 核心栈

建议第一版先接这些：

1. `Polymarket`
2. `Kalshi`
3. `CoinGecko`
4. `Deribit`
5. `Treasury FiscalData`
6. `U.S. Treasury Yield Data`
7. `SEC EDGAR`
8. `Stooq`
9. `CFTC COT`
10. `AkShare`
11. `World Bank`
12. `Eurostat`
13. `ECB`

这套已经足够覆盖：

- 预测市场
- 美股/ETF/指数历史
- 美债与宏观
- crypto 现货与衍生品
- 中国市场基础层
- 全球跨国宏观对比

### 增强模式（只加 2-3 个 key）

如果用户愿意额外配置少量 key，优先顺序：

1. `FRED`
2. `Tushare Pro`
3. `Glassnode`

理由：

- `FRED`：美国宏观最值得补
- `Tushare Pro`：中国数据质量提升最大
- `Glassnode`：BTC 案例里信息价值最高

---

## 八、对产品设计的启发

### 1. 第一版必须支持“零配置可运行”

用户 clone 下来后，即使不填任何 key，也应该能跑。

### 2. 数据源要做成 provider 层

建议统一抽象成：

```python
class SignalProvider:
    def fetch(self, query):
        ...
```

然后分别实现：

- `PolymarketProvider`
- `KalshiProvider`
- `CoinGeckoProvider`
- `DeribitProvider`
- `TreasuryProvider`
- `SecEdgarProvider`
- `StooqProvider`
- `CftcProvider`
- `AkShareProvider`
- `WorldBankProvider`
- `EurostatProvider`
- `EcbProvider`

### 3. 一定要有离线快照测试

因为很多公开源都没有 SLA，或者文档好、体验一般。

建议维护：

- `fixtures/provider_snapshots/`
- `fixtures/scenario_cases/`
- `demo_mode`

这样用户第一次体验不依赖网络，也方便 CI。

---

## 九、最终结论

如果目标是：

> “海外用户和中国用户都能在自己电脑上装几个插件，最好不填 key，就跑起来”

那么第一版最合理的数据路线不是“接最专业的金融 API”，而是：

> **用一组真正零 key、官方或足够稳定的公开源，先把全球版的 market-reading engine 跑起来。**

现阶段最值得优先接入的是：

- `Polymarket`
- `Kalshi`
- `CoinGecko`
- `Deribit`
- `Treasury/FiscalData`
- `SEC EDGAR`
- `Stooq`
- `CFTC COT`
- `AkShare`
- `World Bank`
- `Eurostat`
- `ECB`

其中：

- **预测市场层**：`Polymarket + Kalshi`
- **crypto 层**：`CoinGecko + Deribit`
- **美国宏观骨架**：`Treasury + FiscalData + SEC + CFTC`
- **全球比较层**：`World Bank + Eurostat + ECB`
- **中国市场层**：`AkShare`

这是一个真正可以做到“本地开箱即用、面向全球用户”的第一版数据栈。
