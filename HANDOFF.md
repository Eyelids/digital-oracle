# predict-by-emh 交接文档

## 交接目的

这份文档是给另一个 Cursor 窗口继续迭代用的。

当前已经做出来的是一个 **local-first 的 provider 原型层**，目标不是立刻做完整产品，而是先把：

- 公开数据源接入
- 数据结构标准化
- demo 可直接运行
- fixture / snapshot 风格测试先站住

做成一个可继续扩展的底座。

## 目录说明

当前这个私有目录已经是独立工作区：

- **代码直接放在当前根目录**
- Python package 名仍然是 `predict_by_emh`
- demo / tests 也都已经迁到当前根目录

旧的 `ClawHQ/predict-by-emh/` 只是最初复制来源，不再是当前继续开发的主目录。

## 当前代码状态

已经实现并验证的 provider：

1. `PolymarketProvider`
2. `USTreasuryProvider`
3. `StooqProvider`
4. `DeribitProvider`
5. `KalshiProvider`

公共抽象和网络层：

- `predict_by_emh/providers/base.py`
- `predict_by_emh/http.py`
- `predict_by_emh/providers/prices.py`
- `predict_by_emh/snapshots.py`

### 1. `PolymarketProvider`

文件：

- `predict_by_emh/providers/polymarket.py`
- `demo_polymarket.py`
- `tests/test_polymarket_provider.py`

已经支持：

- 拉活动事件列表
- 按 `slug` 取单个 event
- 按 YES token 拉 orderbook
- 把 `outcomes` / `outcomePrices` / `clobTokenIds` 从原始字符串 JSON 规范化成 dataclass
- 兼容 live API 里 `order=volume24hr` 这种和文档不完全一致的参数

### 2. `USTreasuryProvider`

文件：

- `predict_by_emh/providers/treasury.py`
- `demo_treasury.py`
- `tests/test_treasury_provider.py`

已经支持：

- 官方 Treasury CSV 收益率曲线
- `nominal` / `real` / `bill` / `long_term`
- `yield_for("10Y")`
- `spread("10Y", "2Y")`
- FiscalData 汇率 REST
- 按 `country` / `currency` / `country_currency_desc` 过滤

这块踩过一个真实坑：

- FiscalData 里的中国字段是 `China-Renminbi`
- 不是 `China-Yuan`

所以现在更推荐从 `country=("China", "Japan")` 这种层级查，不要硬编码 description。

### 3. `StooqProvider`

文件：

- `predict_by_emh/providers/stooq.py`
- `demo_stooq.py`
- `tests/test_stooq_provider.py`

已经支持：

- 单 symbol 历史价格下载
- `d` / `w` / `m`
- 日期过滤
- `limit`
- 有 `Volume` 和无 `Volume` 两种 CSV 结构
- 统一转成 `PriceHistory` / `PriceBar`

### 4. `DeribitProvider`

文件：

- `predict_by_emh/providers/deribit.py`
- `demo_deribit.py`
- `tests/test_deribit_provider.py`

已经支持：

- `get_instruments` 拉 futures / options 元数据
- 单 instrument order book
- futures term structure
- option chain summary
- 把 instrument metadata 和 book summary 结果 join 成 dataclass
- 计算相对 perpetual 的 basis / annualized basis

### 5. `KalshiProvider`

文件：

- `predict_by_emh/providers/kalshi.py`
- `demo_kalshi.py`
- `tests/test_kalshi_provider.py`

已经支持：

- `list_markets`
- `get_market`
- `get_event`
- `get_order_book`
- 把 Kalshi 的 cent-priced market snapshot 规范化成 probability 风格字段
- 从 `yes/no` 双边挂单推导 `best_yes_ask` / `best_no_ask`
- 默认通过 `mve_filter=exclude` 排除 multivariate combo 市场

## snapshot / replay 现状

现在已经有一个最小可用的 fixture 录制层：

- `predict_by_emh/snapshots.py`
- `RecordingHttpClient`
- `ReplayHttpClient`

用途：

- 用 live 请求把响应录成标准化 snapshot 文件
- 后续在测试里按 `url + params + payload kind(json/text)` 精确回放

当前这层是通用的，不绑定某个 provider。

典型用法：

```python
from predict_by_emh import RecordingHttpClient, ReplayHttpClient
from predict_by_emh.providers import DeribitProvider

recorder = RecordingHttpClient("tests/fixtures/snapshots")
provider = DeribitProvider(http_client=recorder)
provider.get_order_book("BTC-PERPETUAL")

replay = ReplayHttpClient("tests/fixtures/snapshots")
provider = DeribitProvider(http_client=replay)
provider.get_order_book("BTC-PERPETUAL")
```

这意味着后面继续接 `Kalshi` / `CoinGecko` / `SEC EDGAR` 时，不必再手工拼 fixture 格式，只要先录，再裁剪即可。

## 当前可直接运行的命令

测试：

```bash
python3 -m unittest discover -s tests -q
```

Polymarket demo：

```bash
python3 demo_polymarket.py --limit 5
python3 demo_polymarket.py --slug microstrategy-sell-any-bitcoin-in-2025 --show-book
```

Treasury demo：

```bash
python3 demo_treasury.py --year 2026 --kind nominal --limit 2
python3 demo_treasury.py --year 2026 --kind nominal --limit 2 --fx China --fx Japan --fx-limit 8
python3 demo_treasury.py --year 2026 --kind real --limit 2
```

Stooq demo：

```bash
python3 demo_stooq.py --symbol spy.us --limit 3
python3 demo_stooq.py --symbol eurusd --limit 3
```

Deribit demo：

```bash
python3 demo_deribit.py --view futures --currency BTC
python3 demo_deribit.py --view options --currency BTC --expiration 11MAR26 --limit 8
python3 demo_deribit.py --view book --instrument BTC-PERPETUAL --depth 5
```

Kalshi demo：

```bash
python3 demo_kalshi.py --series KXFED --limit 5
python3 demo_kalshi.py --event KXFED-27APR --limit 5
python3 demo_kalshi.py --ticker KXFED-27APR-T4.25 --show-book --depth 10
```

## 已经确认的工程约束

### 1. 先保持零依赖

当前全部用标准库：

- `urllib`
- `csv`
- `json`
- `unittest`

这是刻意的，方便本地开箱即用。

### 2. 公共源会抖

`predict_by_emh/http.py` 里已经加了轻量 retry。

原因：

- `FiscalData` 出过 EOF / SSL 抖动
- 这类公开源未来还会重复出现类似情况

### 3. 先做 provider，不急着做总调度

当前还没有：

- 统一 query planner
- “问题 -> 应调用哪些 provider” 的自动路由
- 上层 signal scorer / analyzer

这是故意的。现在先把数据面做厚。

## 下一步建议

优先顺序建议如下：

1. 做一个更明确的 provider contract
   - 现在已经有 `SignalProvider`
   - `DeribitProvider` 已经把 “instrument / summary / orderbook / term structure / option chain” 这层边界压出来了
   - `KalshiProvider` 进一步暴露了另一类市场结构：event + laddered binary markets + derived asks
   - 下一步可以考虑再抽一层 capability-oriented interface，但不要先做大重构

2. 把 snapshot / replay 真正接到 provider 开发流程里
   - 当前通用录制/回放工具已经有了
   - 下一步是把 live capture -> fixture 裁剪 -> unittest 这条路径标准化

3. 再考虑 `CoinGecko` 或 `AkShare`
   - `CoinGecko` 补 crypto spot 基础层
   - `AkShare` 补中国市场本地落地

4. 再考虑现货 / 宏观补强
   - `World Bank / Eurostat / ECB`：补全球比较层

## 另一个窗口继续迭代时的建议提示词

可以直接告诉另一个窗口：

```text
先读 `HANDOFF.md`，然后基于当前目录里的 provider 原型继续开发。
当前已有 Polymarket / USTreasury / Stooq / Deribit / Kalshi 五个 provider、demo 和 unittest。
Deribit 已经覆盖 instruments / orderbook / futures term structure / option chain。
Kalshi 已经覆盖 markets / market detail / event / orderbook，并且 orderbook ask 需要从对手边推导。
下一步优先做 provider contract 收敛和 snapshot/replay，而不是先做 planner。
```

## 本次提交应包含什么

建议本次提交只包含这几类内容：

- 当前目录下的原型代码、测试、demo、文档

不应包含：

- `__pycache__`
- `.pyc`
- 仓库里其他无关改动
