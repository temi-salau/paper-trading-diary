"""
Decides hold/partial sell/full sell for a position, combining trend signal,
volatility-adjusted sizing, RSI, ADX, and unrealized P&L.
"""

FULL_SELL_RATIO = 0.1
HOLD_RATIO = 0.9
MIN_BUY_RATIO = 0.15 # higher than FULL_SELL_RATIO, due to risk req more conviction
NEAR_HIGH_THRESHOLD = -0.05  # within 5% of the 6-month high counts as "near"
STRONG_TREND_ADX = 40
TREND_ADX = 25
MAX_POSITION_PCT = 0.05 # Match discretionary rule of no more than 5% of portfolio value

def decide_action(signal, suggested_sell_size, suggested_buy_size, qty, unrealized_pl, rsi, adx):
    if unrealized_pl <= 0:
        if not signal and adx >= 40:
            ratio = suggested_sell_size / qty
            if ratio > FULL_SELL_RATIO:
                return f"partial sell {int(suggested_sell_size)} shares (loss protection override, strong confirmed downtrend)"
        return "hold (loss protection)"

    if signal:
        if adx >= 40 and rsi < 70:
            buy_ratio = suggested_buy_size / qty
            if buy_ratio >= MIN_BUY_RATIO:
                return f"buy more {int(suggested_buy_size)} shares (confirmed uptrend, not overbought)"
        return "hold (bullish signal)"

    sell_ratio = suggested_sell_size / qty

    if sell_ratio <= FULL_SELL_RATIO:
        action = f"full sell {int(suggested_sell_size)} shares"
    elif sell_ratio >= HOLD_RATIO:
        return "hold (change too small)"
    else:
        action = f"partial sell {int(suggested_sell_size)} shares"

    if rsi < 30 and "full sell" in action:
        return f"partial sell {int(suggested_sell_size)} shares (RSI oversold, downgraded from full sell)"

    return f"{action} (confirmed downtrend)"

def decide_enter(signal, adx, rsi, pct_off_high, portfolio_value, current_price):
    if not signal or rsi >= 70:
        return "no entry signal"

    suggested_shares = int((portfolio_value * MAX_POSITION_PCT) / current_price)
    high_note = "near 6-month high" if pct_off_high >= NEAR_HIGH_THRESHOLD else "off recent high"

    if adx >= STRONG_TREND_ADX:
        return f"strong buy {suggested_shares} (confirmed strong uptrend, {high_note}, not overbought)"
    elif adx >= TREND_ADX:
        return f"buy {suggested_shares} (confirmed uptrend, {high_note}, not overbought)"
    
    return "no entry signal"