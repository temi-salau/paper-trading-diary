"""
Connects to Alpaca's paper trading account, pulls the current AAPL position, and combines
it with strategy.py's signal/volatility outputs to decide whether to hold, partially sell,
or fully sell, based on trend direction, volatility-adjusted sizing, and profit/loss.
"""

from dotenv import load_dotenv
import os
from alpaca.trading.client import TradingClient
from strategy import decide_action, signals

load_dotenv()

api_key = os.getenv("alpaca_api_key")
secret_key = os.getenv("alpaca_secret_key")

trading_client = TradingClient(api_key, secret_key, paper=True)
print("Connected to Alpaca API successfully!")

positions = trading_client.get_all_positions()
position = positions[0] # single-symbol only for now would need restructuring for multiple holdings

symbol = position.symbol
qty = float(position.qty)
unrealized_pl = float(position.unrealized_pl)

today_signal = signals["signal"].iloc[-1] # most recent row's signal, based on the 3/7 crossover pair
today_suggested_size = signals["suggested_size"].iloc[-1] # volatility and trend strength adjusted sizing for today
today_rsi = signals["rsi"].iloc[-1]
today_adx = signals["adx"].iloc[-1]
action = decide_action(today_signal, today_suggested_size, qty, unrealized_pl, today_rsi, today_adx)
print(f"{symbol}: {action}")