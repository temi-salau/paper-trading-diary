"""
Decides hold/partial sell/full sell for a position, combining trend signal,
volatility-adjusted sizing, RSI, ADX, and unrealized P&L.
"""

FULL_SELL_RATIO = 0.1
HOLD_RATIO = 0.9
MIN_BUY_RATIO = 0.15 # higher than FULL_SELL_RATIO, due to risk req more conviction

def decide_action(signal, suggested_sell_size, suggested_buy_size, qty, unrealized_pl, rsi, adx):
    if unrealized_pl <= 0:
        if not signal and adx >= 40:
            ratio = suggested_sell_size / qty
            if ratio > FULL_SELL_RATIO:
                return "partial sell (loss protection override, strong confirmed downtrend)"
        return "hold (loss protection)"

    if signal:
        if adx >= 40 and rsi < 70:
            buy_ratio = suggested_buy_size / qty
            if buy_ratio >= MIN_BUY_RATIO:
                return "buy more (confirmed uptrend, not overbought)"
        return "hold (bullish signal)"

    sell_ratio = suggested_sell_size / qty

    if sell_ratio <= FULL_SELL_RATIO:
        action = "full sell"
    elif sell_ratio >= HOLD_RATIO:
        return "hold (change too small)"
    else:
        action = "partial sell"

    if rsi < 30 and action == "full sell":
        return "partial sell (RSI oversold, downgraded from full sell)"

    return action