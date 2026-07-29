"""
Fetches AAPL daily price data via Alpaca and computes a 10/20-day moving average
crossover signal. Outputs a comparison table showing when short-term momentum
crosses above/below the longer-term trend.
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
print(close)

short_ma = close.rolling(window=10).mean() # fast-reacting, recent trend
long_ma = close.rolling(window=20).mean() # slower, broader trend baseline

comparison = pd.DataFrame({
    "close": close,
    "short_ma": short_ma,
    "long_ma": long_ma
})
comparison["signal"] = comparison["short_ma"] > comparison["long_ma"] # True = bullish crossover state

print(comparison)