import pandas as pd

from fvg_quant.backtest import run_backtest
from fvg_quant.strategy import FVGConfig, generate_trade_signals


def _ohlc(index, base=100.0):
    data = []
    price = base
    for i, _ in enumerate(index):
        op = price
        hi = op + 2 + (i % 3)
        lo = op - 2
        cl = op + (1 if i % 2 == 0 else -0.5)
        price = cl + 0.3
        data.append((op, hi, lo, cl, 1000))
    return pd.DataFrame(data, index=index, columns=["open", "high", "low", "close", "volume"])


def test_signal_generation_returns_list():
    idx_4h = pd.date_range("2024-01-01", periods=80, freq="4h", tz="UTC")
    idx_1h = pd.date_range("2024-01-01", periods=300, freq="1h", tz="UTC")
    idx_15m = pd.date_range("2024-01-01", periods=500, freq="15min", tz="UTC")

    df_4h = _ohlc(idx_4h, 100)
    df_1h = _ohlc(idx_1h, 120)
    df_15m = _ohlc(idx_15m, 140)

    signals = generate_trade_signals(df_4h, df_1h, df_15m, FVGConfig())
    assert isinstance(signals, list)


def test_backtest_runs():
    idx_4h = pd.date_range("2024-01-01", periods=80, freq="4h", tz="UTC")
    idx_1h = pd.date_range("2024-01-01", periods=300, freq="1h", tz="UTC")
    idx_15m = pd.date_range("2024-01-01", periods=500, freq="15min", tz="UTC")

    df_4h = _ohlc(idx_4h, 100)
    df_1h = _ohlc(idx_1h, 120)
    df_15m = _ohlc(idx_15m, 140)

    result = run_backtest(df_4h, df_1h, df_15m)
    assert result.equity_curve.iloc[-1] > 0
