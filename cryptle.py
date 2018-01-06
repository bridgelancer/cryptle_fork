import math
import numpy as np
import pandas as pd
import requests as req
from datetime import date
from time import time

# @stripped, Trading pairs info
# Assume there is signature and API_key

# ALL "data" variables (except those used by pd) need to be substituted by suitable feed structures

# Check ORDER STATUS/OPEN ORDERS?
# WIll we CANCEL ORDER?


def detect_entry_signal(price_window_5, price_window_8):
# context.prices should be changed to relevant data structure
    """
    Compute high and low for breakout price
    """
    if price_window_5.avg > price_window_8.avg:
        # Limit buy (maybe market price + 0.3%?)
        # PLACEHOLDER
        res = request.post('https://www.bitstamp.net/api/v2/buy/xxxxxx/', param = {'key': '', 'signature': '', 'nonce': '', 'amount': '', 'price': price * 1.003, 'limit_price': price * 0.98})
        
        
def compute_exit_signal(price_window_5, price_window_8):
    """
    Determine exit signal and place market sell order
    """
    res = request.post('https://www.bitstamp.net/api/user_transactions/', param = ('key': '', 'signature': '', 'nonce': '', 'limit': ''))

    for item in res.json(): # check user transactions
        order_id = item['order_id'] # this needs to be revised
        if order_id == id and live_min_price_5.avg < live_min_price_8.avg:
            # Market sell
            # PLACEHOLDER
            res = request.post('https://www.bitstamp.net/api/v2/sell/market/xxxxxx/', param = {'key': '', 'signature': '', 'nonce': '', 'amount': ''}) # amount should be equivalent to the amount bought
            
def compute_average_true_ranges(price_window):
    """
    Compute ATR, aka N
    """
    # taking time period as 5 currently
    timeperiod = 5

    true_high = max(price_window.high, price_window.close)
    true_low = min(price_window.low, price_window.close)

    TR = true_high - true_low
    TR_p = price_window.high_p - price_window.low_p

    return (TR + TR_p * (timeperiod - 1)) / timeperiod


def compute_trade_sizes(price_window):
    """
    how many unit equivilants to 1% of equity
    """
    dollar_volatility =
           2 * compute_average_true_ranges(price_window) #multiplier * N

        return account_balance/dollar_volatility #no account_balance
