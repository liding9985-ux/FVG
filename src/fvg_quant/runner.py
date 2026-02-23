from __future__ import annotations

from dataclasses import dataclass

from .binance_client import BinanceConfig, BinanceGateway
from .strategy import FVGConfig, generate_trade_signals


@dataclass
class RunnerConfig:
    symbol: str = "BTC/USDT"
    trade_amount: float = 0.001


def run_once(binance_config: BinanceConfig, runner_config: RunnerConfig, strategy_config: FVGConfig = FVGConfig()):
    gateway = BinanceGateway(binance_config)
    df_4h = gateway.fetch_ohlcv_df(runner_config.symbol, "4h", limit=400)
    df_1h = gateway.fetch_ohlcv_df(runner_config.symbol, "1h", limit=600)
    df_15m = gateway.fetch_ohlcv_df(runner_config.symbol, "15m", limit=800)

    signals = generate_trade_signals(df_4h, df_1h, df_15m, strategy_config)
    if not signals:
        return {"status": "no_signal"}

    latest = signals[-1]
    side = "buy" if latest.side == "long" else "sell"
    order = gateway.place_order(runner_config.symbol, side=side, amount=runner_config.trade_amount)
    return {"status": "ordered", "signal": latest, "order": order}
