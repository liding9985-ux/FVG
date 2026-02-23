from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import ccxt
import pandas as pd


@dataclass
class BinanceConfig:
    api_key: str = ""
    api_secret: str = ""
    testnet: bool = True


class BinanceGateway:
    def __init__(self, config: BinanceConfig):
        self.exchange = ccxt.binance(
            {
                "apiKey": config.api_key,
                "secret": config.api_secret,
                "enableRateLimit": True,
                "options": {"defaultType": "future"},
            }
        )
        if config.testnet:
            self.exchange.set_sandbox_mode(True)

    def fetch_ohlcv_df(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        rows = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        return df.set_index("timestamp")

    def place_order(self, symbol: str, side: str, amount: float, order_type: str = "market", **kwargs: Any) -> dict[str, Any]:
        return self.exchange.create_order(symbol=symbol, type=order_type, side=side, amount=amount, params=kwargs)
