"""
Fetches AAPL daily price data via Alpaca and computes a 10/20-day moving average
crossover signal, a faster 3/7 pair for comparison, and an ATR-based volatility ratio
to detect single-day price shocks the MA crossover misses.
"""

from dotenv import load_dotenv
import os
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

load_dotenv()

api_key = os.getenv("alpaca_api_key")
secret_key = os.getenv("alpaca_secret_key")

data_client = StockHistoricalDataClient(api_key, secret_key)

start = datetime.now() - timedelta(days=60) # 60 days gives enough history for a 20-day MA with room to spare
end = datetime.now()

requests = StockBarsRequest(
    symbol_or_symbols="AAPL",
    start=start,
    end=end,
    timeframe=TimeFrame.Day,
    feed=DataFeed.IEX # free-tier
)

bars = data_client.get_stock_bars(requests)
close = bars.df["close"]
# print(close)

short_ma = close.rolling(window=10).mean() # fast-reacting, recent trend
long_ma = close.rolling(window=20).mean() # slower, broader trend baseline

comparison = pd.DataFrame({
    "close": close,
    "short_ma": short_ma,
    "long_ma": long_ma
})
comparison["signal"] = comparison["short_ma"] > comparison["long_ma"] # True = bullish crossover state

print(comparison)

# faster pair tested to check if window length alone explains the 07-31 lag
short_ma_3 = close.rolling(window=3).mean()
long_ma_7 = close.rolling(window=7).mean()

comparison2 = pd.DataFrame({
    "close": close,
    "short_ma": short_ma_3,
    "long_ma": long_ma_7
})

comparison2["signal"] = comparison2["short_ma"] > comparison2["long_ma"]

print(comparison2)

ohlc = bars.df[["high", "low", "close"]].copy()

ohlc["prev_close"] = ohlc["close"].shift(1)

ohlc["tr1"] = ohlc["high"] - ohlc["low"]
ohlc["tr2"] = (ohlc["high"] - ohlc["prev_close"]).abs()
ohlc["tr3"] = (ohlc["low"] - ohlc["prev_close"]).abs()

ohlc["true_range"] = ohlc[["tr1", "tr2", "tr3"]].max(axis=1) # max of the three captures overnight gaps, not just intraday range
ohlc["atr"] = ohlc["true_range"].rolling(window=14).mean() # 14-day is the standard ATR convention
ohlc["tr_atr_ratio"] = ohlc["true_range"] / ohlc["atr"].shift(1) # shift(1) so today's move is compared against yesterday's ATR, not today's

print(ohlc)