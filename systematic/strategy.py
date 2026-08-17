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

VOLATILITY_THRESHOLD = 2
FULL_SELL_RATIO = 0.1
HOLD_RATIO = 0.9

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
comparison["signal"] = comparison["short_ma"] > comparison["long_ma"] # kept for reference: 10/20 pair lagged the 07-31 shock by 4 days hence switching to 3/7 below

# faster pair tested to check if window length alone explains the 07-31 lag
short_ma_3 = close.rolling(window=3).mean()
long_ma_7 = close.rolling(window=7).mean()

comparison2 = pd.DataFrame({
    "close": close,
    "short_ma": short_ma_3,
    "long_ma": long_ma_7
})

comparison2["signal"] = comparison2["short_ma"] > comparison2["long_ma"]

ohlc = bars.df[["high", "low", "close"]].copy()

ohlc["prev_close"] = ohlc["close"].shift(1)

ohlc["tr1"] = ohlc["high"] - ohlc["low"]
ohlc["tr2"] = (ohlc["high"] - ohlc["prev_close"]).abs()
ohlc["tr3"] = (ohlc["low"] - ohlc["prev_close"]).abs()

ohlc["true_range"] = ohlc[["tr1", "tr2", "tr3"]].max(axis=1) # max of the three captures overnight gaps, not just intraday range
ohlc["atr"] = ohlc["true_range"].rolling(window=14).mean() # 14-day is the standard ATR convention
ohlc["tr_atr_ratio"] = ohlc["true_range"] / ohlc["atr"].shift(1) # shift(1) so today's move is compared against yesterday's ATR, not today's

ohlc["unusual_volatility"] = ohlc["tr_atr_ratio"] > VOLATILITY_THRESHOLD

ohlc["size_multiplier"] = (VOLATILITY_THRESHOLD / ohlc["tr_atr_ratio"]).clip(upper=1)
BASE_POSITION_SIZE = 5

delta = close.diff()
gains = delta.where(delta > 0, 0)
losses = -delta.where(delta < 0, 0)
avg_gain = gains.rolling(window=14).mean()
avg_loss = losses.rolling(window=14).mean()
rsi = 100 - (100 / (1 + avg_gain/avg_loss)) # >70 overbought, <30 oversold

ohlc["up_move"] = ohlc["high"] - ohlc["high"].shift(1)
ohlc["down_move"] = ohlc["low"].shift(1) - ohlc["low"]

# only counts if move is both positive and bigger than the other move
ohlc["plus_dm"] = ((ohlc["up_move"] > ohlc["down_move"]) & (ohlc["up_move"] > 0)) * ohlc["up_move"]
ohlc["minus_dm"] = ((ohlc["down_move"] > ohlc["up_move"]) & (ohlc["down_move"] > 0)) * ohlc["down_move"]

# upwards and downwards pressure scaled by volatility
smoothed_plus_dm = ohlc["plus_dm"].rolling(window=14).mean()
smoothed_minus_dm = ohlc["minus_dm"].rolling(window=14).mean()

plus_di = 100 * (smoothed_plus_dm / ohlc["atr"])
minus_di = 100 * (smoothed_minus_dm / ohlc["atr"])

dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di) # how far apart the two directions are regardless of which dominates
adx = dx.rolling(window=14).mean() # smoothed trend strength (Investopedia convention): <25 weak/no trend, 25-50 strong, 50-75 very strong, 75-100 extremely strong

ohlc["rsi"] = rsi
ohlc["adx"] = adx

adx_multiplier = (ohlc["adx"] / 25).clip(upper=1)
ohlc["final_multiplier"] = ohlc["size_multiplier"] * adx_multiplier
ohlc["suggested_size"] = (BASE_POSITION_SIZE * ohlc["final_multiplier"]).round()

signals = pd.merge(comparison2, ohlc, left_index=True, right_index=True)
print(signals[["close_x", "signal", "tr_atr_ratio", "rsi", "adx", "suggested_size"]])

def decide_action(signal, suggested_size, qty, unrealized_pl, rsi):
    if unrealized_pl <= 0:
        return "hold (loss protection)"

    if signal:
        return "hold (bullish signal)"

    ratio = suggested_size / qty

    if ratio <= FULL_SELL_RATIO:
        action = "full sell"
    elif ratio >= HOLD_RATIO:
        return "hold (change too small)"
    else:
        action = "partial sell"

    if rsi < 30 and action == "full sell":
        return "partial sell (RSI oversold, downgraded from full sell)"

    return action