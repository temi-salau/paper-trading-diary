"""
Connects to Alpaca and fetches AAPL price data (close prices and full OHLC),
used by indicators.py to compute trading signals.
"""

from dotenv import load_dotenv
import os
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

load_dotenv()

api_key = os.getenv("alpaca_api_key")
secret_key = os.getenv("alpaca_secret_key")

data_client = StockHistoricalDataClient(api_key, secret_key)

start = datetime.now() - timedelta(days=180) # ~6 months (approx. max holding horizon)
end = datetime.now()

def get_price_data(symbol):
    requests = StockBarsRequest(
        symbol_or_symbols=symbol,
        start=start,
        end=end,
        timeframe=TimeFrame.Day,
        feed=DataFeed.IEX # free-tier
    )

    bars = data_client.get_stock_bars(requests)
    close = bars.df["close"]
    ohlc = bars.df[["high", "low", "close"]].copy()
    return close, ohlc