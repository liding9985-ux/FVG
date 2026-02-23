from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .indicators import atr


@dataclass
class FVGZone:
    direction: int  # 1 bullish, -1 bearish
    lower: float
    upper: float
    created_at: pd.Timestamp
    active: bool = True



def detect_fvg_zones(df_1h: pd.DataFrame, atr_ratio: float = 0.2, atr_length: int = 14) -> list[FVGZone]:
    zones: list[FVGZone] = []
    df = df_1h.copy()
    df["atr"] = atr(df, atr_length)

    for i in range(2, len(df)):
        current = df.iloc[i]
        prior_2 = df.iloc[i - 2]
        threshold = (current["atr"] or 0) * atr_ratio

        # bullish FVG: low[i] > high[i-2]
        if current["low"] > prior_2["high"]:
            gap = current["low"] - prior_2["high"]
            if gap >= threshold:
                zones.append(
                    FVGZone(
                        direction=1,
                        lower=prior_2["high"],
                        upper=current["low"],
                        created_at=df.index[i],
                    )
                )

        # bearish FVG: high[i] < low[i-2]
        if current["high"] < prior_2["low"]:
            gap = prior_2["low"] - current["high"]
            if gap >= threshold:
                zones.append(
                    FVGZone(
                        direction=-1,
                        lower=current["high"],
                        upper=prior_2["low"],
                        created_at=df.index[i],
                    )
                )

    return zones


def deactivate_filled_zones(zones: list[FVGZone], price_bar: pd.Series) -> None:
    for zone in zones:
        if not zone.active:
            continue
        # If candle fully crosses zone boundaries, consider it fully filled.
        if price_bar["low"] <= zone.lower and price_bar["high"] >= zone.upper:
            zone.active = False
