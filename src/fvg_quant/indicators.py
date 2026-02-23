from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(length).mean()


def swing_points(df: pd.DataFrame, lookback: int = 3) -> tuple[pd.Series, pd.Series]:
    highs = df["high"]
    lows = df["low"]
    pivot_high = highs[(highs.shift(lookback) < highs) & (highs.shift(-lookback) < highs)]
    pivot_low = lows[(lows.shift(lookback) > lows) & (lows.shift(-lookback) > lows)]
    return pivot_high, pivot_low


def structure_bias(df_4h: pd.DataFrame, lookback: int = 3) -> pd.Series:
    pivot_high, pivot_low = swing_points(df_4h, lookback)
    last_high = pivot_high.ffill()
    prev_high = pivot_high.shift(1).ffill()
    last_low = pivot_low.ffill()
    prev_low = pivot_low.shift(1).ffill()

    bullish = (last_high > prev_high) & (last_low > prev_low)
    bearish = (last_high < prev_high) & (last_low < prev_low)
    bias = np.where(bullish, 1, np.where(bearish, -1, 0))
    return pd.Series(bias, index=df_4h.index, name="structure_bias")


def engulfing(df: pd.DataFrame) -> pd.DataFrame:
    prev_open = df["open"].shift(1)
    prev_close = df["close"].shift(1)

    bullish = (
        (df["close"] > df["open"])
        & (prev_close < prev_open)
        & (df["open"] <= prev_close)
        & (df["close"] >= prev_open)
    )

    bearish = (
        (df["close"] < df["open"])
        & (prev_close > prev_open)
        & (df["open"] >= prev_close)
        & (df["close"] <= prev_open)
    )

    return pd.DataFrame({"bullish_engulfing": bullish, "bearish_engulfing": bearish}, index=df.index)
