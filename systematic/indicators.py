"""
Computes trading signals from raw price data: moving average crossovers, ATR-based
volatility, RSI, and ADX, combined into a single signals table.
"""

import pandas as pd

VOLATILITY_THRESHOLD = 2
BASE_POSITION_SIZE = 5

def get_signals(close, ohlc):
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

    ohlc["prev_close"] = ohlc["close"].shift(1)
    ohlc["tr1"] = ohlc["high"] - ohlc["low"]
    ohlc["tr2"] = (ohlc["high"] - ohlc["prev_close"]).abs()
    ohlc["tr3"] = (ohlc["low"] - ohlc["prev_close"]).abs()
    ohlc["true_range"] = ohlc[["tr1", "tr2", "tr3"]].max(axis=1) # max of the three captures overnight gaps, not just intraday range
    ohlc["atr"] = ohlc["true_range"].rolling(window=14).mean() # 14-day is the standard ATR convention
    ohlc["tr_atr_ratio"] = ohlc["true_range"] / ohlc["atr"].shift(1) # shift(1) so today's move is compared against yesterday's ATR, not today's
    ohlc["unusual_volatility"] = ohlc["tr_atr_ratio"] > VOLATILITY_THRESHOLD
    ohlc["size_multiplier"] = (VOLATILITY_THRESHOLD / ohlc["tr_atr_ratio"]).clip(upper=1)

    # RSI
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

    # ADX
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
    ohlc["suggested_sell_size"] = (BASE_POSITION_SIZE * ohlc["final_multiplier"]).round()

    buy_confidence_multiplier = (ohlc["adx"] / 40).clip(upper=2) # capped at 2x base size for a very strong trend
    ohlc["suggested_buy_size"] = (BASE_POSITION_SIZE * buy_confidence_multiplier).round()

    signals = pd.merge(comparison2, ohlc, left_index=True, right_index=True)
    return signals