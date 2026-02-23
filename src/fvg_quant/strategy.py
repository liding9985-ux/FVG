from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .fvg import FVGZone, deactivate_filled_zones, detect_fvg_zones
from .indicators import ema, engulfing, structure_bias


@dataclass
class FVGConfig:
    atr_ratio: float = 0.2
    ema_len: int = 200
    structure_lookback: int = 3


@dataclass
class Signal:
    timestamp: pd.Timestamp
    side: str
    price: float
    stop_loss: float
    take_profit: float
    reason: str


def _hourly_bias(df_4h: pd.DataFrame, config: FVGConfig) -> pd.Series:
    out = df_4h.copy()
    out["ema"] = ema(out["close"], config.ema_len)
    out["ema_bias"] = (out["close"] > out["ema"]).astype(int) - (out["close"] < out["ema"]).astype(int)
    out["structure_bias"] = structure_bias(out, config.structure_lookback)
    out["combined_bias"] = out[["ema_bias", "structure_bias"]].min(axis=1)
    out.loc[(out["ema_bias"] == -1) & (out["structure_bias"] == -1), "combined_bias"] = -1
    return out["combined_bias"]


def generate_trade_signals(
    df_4h: pd.DataFrame,
    df_1h: pd.DataFrame,
    df_15m: pd.DataFrame,
    config: FVGConfig = FVGConfig(),
) -> list[Signal]:
    bias_4h = _hourly_bias(df_4h, config).reindex(df_15m.index, method="ffill").fillna(0)
    zones = detect_fvg_zones(df_1h, config.atr_ratio)
    pat = engulfing(df_15m)

    signals: list[Signal] = []

    for ts, row in df_15m.iterrows():
        deactivate_filled_zones(zones, row)
        regime = bias_4h.loc[ts]
        active_zones = [z for z in zones if z.active and z.created_at <= ts]

        for z in active_zones:
            touched = row["low"] <= z.upper and row["high"] >= z.lower
            if not touched:
                continue

            # 15m trigger filters
            higher_low = row["low"] >= df_15m["low"].shift(1).loc[ts]
            lower_high = row["high"] <= df_15m["high"].shift(1).loc[ts]

            if z.direction == 1 and regime == 1 and pat.loc[ts, "bullish_engulfing"] and higher_low:
                entry = row["close"]
                sl = min(z.lower, row["low"])
                tp = entry + 2 * (entry - sl)
                signals.append(Signal(ts, "long", entry, sl, tp, "4H bull + 1H FVG + 15M engulfing"))
                z.active = False
                break

            if z.direction == -1 and regime == -1 and pat.loc[ts, "bearish_engulfing"] and lower_high:
                entry = row["close"]
                sl = max(z.upper, row["high"])
                tp = entry - 2 * (sl - entry)
                signals.append(Signal(ts, "short", entry, sl, tp, "4H bear + 1H FVG + 15M engulfing"))
                z.active = False
                break

    return signals
