# FVG Quant（币安量化 + 回测框架）

这是一个可扩展的多周期量化交易框架，针对你提出的思路落地：

- **4H 趋势判定（Bias Engine）**：结构趋势 + EMA200 双过滤
- **1H FVG 识别（ICT 定义）**：支持 ATR 比例过滤 + 被完全填补后失效
- **15M 入场触发**：回到 FVG 区域后，必须配合吞没信号 + 结构不破坏
- **回测模块**：资金管理、手续费、胜率、回撤、权益曲线
- **Binance 网关**：支持 testnet/sandbox，实盘前可先联调

## 1. 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 2. 策略逻辑映射

### 4H Bias Engine

1. **结构趋势**
   - Higher High + Higher Low => 多头
   - Lower High + Lower Low => 空头
2. **EMA 过滤**
   - Close > EMA200 => 多头偏向
   - Close < EMA200 => 空头偏向
3. **组合过滤**
   - 两者同向才放行（`combined_bias`）

### 1H FVG（ICT）

- Bullish FVG: `low[i] > high[i-2]`
- Bearish FVG: `high[i] < low[i-2]`
- Gap 过滤：`gap >= ATR * atr_ratio`
- 完全填补：若 K 线 low <= zone.lower 且 high >= zone.upper，则 zone 失效

### 15M 入场

当价格回到有效 FVG 区域后：

- 做多：4H 为多、15M 看涨吞没、且当前低点不低于前低
- 做空：4H 为空、15M 看跌吞没、且当前高点不高于前高

> 默认不是“触碰就进”，而是“触碰 + 触发信号”才进。

## 3. 快速回测示例

```python
from fvg_quant.backtest import run_backtest
from fvg_quant.strategy import FVGConfig
from fvg_quant.binance_client import BinanceGateway, BinanceConfig

gateway = BinanceGateway(BinanceConfig(testnet=True))
df_4h = gateway.fetch_ohlcv_df("BTC/USDT", "4h", limit=400)
df_1h = gateway.fetch_ohlcv_df("BTC/USDT", "1h", limit=600)
df_15m = gateway.fetch_ohlcv_df("BTC/USDT", "15m", limit=800)

result = run_backtest(df_4h, df_1h, df_15m, strategy_config=FVGConfig())
print(result.total_return, result.win_rate, result.max_drawdown)
```

## 4. 运行单次实盘流程（建议先 testnet）

```python
from fvg_quant.runner import run_once, RunnerConfig
from fvg_quant.binance_client import BinanceConfig

resp = run_once(
    BinanceConfig(api_key="xxx", api_secret="xxx", testnet=True),
    RunnerConfig(symbol="BTC/USDT", trade_amount=0.001),
)
print(resp)
```

## 5. 你可以继续迭代的方向（经验建议）

1. 入场增加 BOS/CHOCH 检测（替代当前“低点不创新低”简化版）
2. 加入会话过滤（伦敦/纽约）和高影响新闻避让
3. 分批止盈（1R/2R/3R）+ 追踪止损（ATR trailing）
4. 增加组合风控：日内最大亏损、连续亏损熔断、相关性限仓
5. 回测升级为事件驱动撮合（考虑滑点、盘口深度、资金费率）

## 6. 风险提示

- 本项目用于研究与教育，不构成投资建议。
- 实盘前请进行参数稳定性测试、Walk-forward、蒙特卡洛重采样。
