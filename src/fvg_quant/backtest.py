from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .strategy import FVGConfig, Signal, generate_trade_signals


@dataclass
class BacktestConfig:
    initial_cash: float = 10_000
    risk_per_trade: float = 0.01
    fee_rate: float = 0.0004


@dataclass
class TradeRecord:
    timestamp: pd.Timestamp
    side: str
    entry: float
    exit: float
    pnl: float


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: list[TradeRecord]
    total_return: float
    win_rate: float
    max_drawdown: float


def _simulate_exit(signal: Signal, future: pd.DataFrame) -> float:
    for _, row in future.iterrows():
        if signal.side == "long":
            if row["low"] <= signal.stop_loss:
                return signal.stop_loss
            if row["high"] >= signal.take_profit:
                return signal.take_profit
        else:
            if row["high"] >= signal.stop_loss:
                return signal.stop_loss
            if row["low"] <= signal.take_profit:
                return signal.take_profit
    return future.iloc[-1]["close"] if not future.empty else signal.price


def run_backtest(
    df_4h: pd.DataFrame,
    df_1h: pd.DataFrame,
    df_15m: pd.DataFrame,
    strategy_config: FVGConfig = FVGConfig(),
    backtest_config: BacktestConfig = BacktestConfig(),
) -> BacktestResult:
    signals = generate_trade_signals(df_4h, df_1h, df_15m, strategy_config)

    equity = backtest_config.initial_cash
    curve = []
    trades: list[TradeRecord] = []

    for signal in signals:
        idx = df_15m.index.get_indexer([signal.timestamp])[0]
        future = df_15m.iloc[idx + 1 : idx + 30]  # hold up to ~7.5 hours

        exit_price = _simulate_exit(signal, future)
        risk_amount = equity * backtest_config.risk_per_trade
        stop_dist = abs(signal.price - signal.stop_loss)
        if stop_dist == 0:
            continue
        qty = risk_amount / stop_dist

        gross = (exit_price - signal.price) * qty if signal.side == "long" else (signal.price - exit_price) * qty
        fees = (signal.price + exit_price) * qty * backtest_config.fee_rate
        pnl = gross - fees

        equity += pnl
        curve.append((signal.timestamp, equity))
        trades.append(TradeRecord(signal.timestamp, signal.side, signal.price, exit_price, pnl))

    equity_curve = pd.Series(dict(curve), dtype=float)
    if equity_curve.empty:
        equity_curve = pd.Series([backtest_config.initial_cash])

    roll_max = equity_curve.cummax()
    drawdown = (equity_curve - roll_max) / roll_max

    wins = [t for t in trades if t.pnl > 0]
    total_return = (equity_curve.iloc[-1] / backtest_config.initial_cash) - 1
    win_rate = len(wins) / len(trades) if trades else 0
    max_drawdown = drawdown.min() if not drawdown.empty else 0

    return BacktestResult(equity_curve, trades, total_return, win_rate, max_drawdown)
