"""
Decides hold/partial sell/full sell for a position, combining trend signal,
volatility-adjusted sizing, RSI, ADX, and unrealized P&L.
"""

FULL_SELL_RATIO = 0.1
HOLD_RATIO = 0.9

def decide_action(signal, suggested_size, qty, unrealized_pl, rsi, adx):
    if unrealized_pl <= 0:
        if not signal and adx >= 40:
            ratio = suggested_size / qty
            if ratio > FULL_SELL_RATIO:
                return "partial sell (loss protection override, strong confirmed downtrend)"
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