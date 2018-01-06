import math
import numpy as np
import pandas as pd
import requests as req
from datetime import date
from time import time
from talib import ATR

# @stripped, Trading pairs info
# Assume there is signature and API_key

# ALL "data" variables (except those used by pd) need to be substituted by suitable feed structures

# Check ORDER STATUS/OPEN ORDERS?
# WIll we CANCEL ORDER?

class context:
    """
    Initialize parameters.
    """

    def __init__(self):
        self.symbols = [
            'BTC',
            'XRP',
            'ETH'
        ]

        self.required_information = [
            'keep track or trade', # trading or keeping track the performance #format: keep_track/trade
            'scale-in stage', #0-4
            'quantity', #ok only have value when TRADING
            'avg price', #ok only have value when TRADING
            'initial entry time',
            'second entry time',
            'third entry time',
            'fourth entry time',
            'stop loss price',
            'exit price', #ok
            'ATR', #ok
            'unit size', #ok
            'strat 2 long breakout price', #ok
            'strat 2 short breakout price', #ok
        ]

        #creating a Master Table
        self.MT= pd.DataFrame(data = None, index = context.symbols, columns = context.required_information)
        self.MT'scale-in stage'] = 0

        #initializations
        self.latest_trade_orders={}
        self.latest_stop_orders={}

        # Breakout and exit signals
        self.strat_one_breakout = 20
        self.strat_one_exit = 10
        
        self.strat_two_breakout = 55
        self.strat_two_exit = 20

        # Risk
        self.tradable_capital = context.portfolio.starting_cash
        self.capital_risk_per_trade = 0.01
        self.capital_lost_multiplier = 2

        self.market_risk_limit = 4
        self.stop_loss_in_N = 2

        # Order
        self.open = 0
        self.filled = 1
        self.canceled = 2
        self.rejected = 3


# @ USER TRANSACTIONS - keep track of performance in fixed interval

def compute_breakout_price(context, data):
# context.prices should be changed to relevant data structure
    """
    Compute high and low for breakout price
    """
    for sym in context.symbols:
        context.MT.loc[sym]['strat 1 long breakout price'] = context.prices\
            .loc[sym, 'high']\
            [-context.strat_one_breakout-1:-1]\
            .max()
        context.MT.loc[sym]['strat 2 long breakout price'] = context.prices\
            .loc[sym, 'high']\
            [-context.strat_two_breakout-1:-1]\
            .max()
        
        context.MT.loc[sym]['strat 1 short breakout price'] = context.prices\
            .loc[sym, 'low']\
            [-context.strat_one_breakout-1:-1]\
            .min()
        context.MT.loc[sym]['strat 2 short breakout price'] = context.prices\
            .loc[sym, 'low']\
            [-context.strat_two_breakout-1:-1]\
            .min()

def compute_exit_price(context,data):
    """
    Compute Exit Price
    """
    exit_prices[sym]['strat_one_long'] = context.prices.loc[sym, 'low']\
        [-context.strat_one_exit-1:-1].min()

    exit_prices[sym]['strat_one_short'] = context.prices.loc[sym, 'high']\
        [-context.strat_one_exit-1:-1].max()

    exit_prices[sym]['strat_two_long'] = context.prices.loc[sym, 'low']\
        [-context.strat_two_exit-1:-1].min()

    exit_prices[sym]['strat_two_short'] = context.prices.loc[sym, 'high']\
        [-context.strat_two_exit-1:-1].max()
    
    for sym in context.symbols:
        context.MT['exit price'] = exit_prices[sym]\
            [context.MT[sym]['type of breakout']]

def compute_average_true_ranges(context, data):
    """
    Compute ATR, aka N
    """

    rolling_window = context.strat_one_breakout+1
    moving_average = context.strat_one_breakout

    for sym in context.symbols:
        context.MT[sym]['ATR'] = ATR(
            context.prices.loc[sym, 'high'][-rolling_window:],
            context.prices.loc[sym, 'low'][-rolling_window:],
            context.prices.loc[sym, 'close'][-rolling_window:],
            timeperiod=moving_average
        )[-1]


def compute_trade_sizes(context, data):
    """
    how many unit equivilants to 1% of equity
    """
    for sym in context.symbols:
        dollar_volatility = context.contracts[sym].multiplier\
            * context.MT[sym]['ATR']

        context.MT[sym]['unit size'] = int(context.tradable_capital/dollar_volatility)

def update_risks(context,data):
    """
    Calculate long and short risk and calculate quota for long and short
    """

    tradingMT = context.MT[context.MT['keep track or trade'] == 'trade']
    long_risk_numbers = [x for x in tradingMT['scale-in stage'] if x > 0]
    short_risk_numbers = [x for x in tradingMT['scale-in stage'] if x < 0]

    context.long_risk = sum(long_risk_numbers)
    context.short_risk = sum(short_risk_numbers)

    context.long_quota = context.direction_risk_limit - context.long_risk
    context.short_quota = context.direction_risk_limit - context. short_risk
# @Buy limit order
def detect_entry_signals(context,data):
    """
    Place limit orders when reach breakout
    hirachy of entry signals: strat 1 > strat 2 > keep track
    """
    for sym in context.symbols:

        if context.MT[sym]['scale-in stage'] != 0:
            continue
    
        long_or_short = 0
        current_price = data.current(context.cfutures[sym], 'price') #needs to be changed

        #check strat 2 breakout
        if(true):
            if (context.long_quota > 0 and
                current_price >= context.MT[sym]['strat 2 long breakout price']):

                context.MT[sym]['scale-in stage'] = 1
                context.MT[sym]['type of breakout'] = 'strat_two_long'
                context.MT[sym]['keep track or trade']= 'trade'
                context.long_quota -= 1
                long_or_short = 1

            else if (context.short_quota > 0 and
                     current_price <= context.MT[sym]['strat 2 short breakout price']):
                       
                context.MT[sym]['scale-in stage'] = -1
                context.MT[sym]['type of breakout'] = 'strat_two_short'
                context.MT[sym]['keep track or trade']= 'trade'
                context.short_quota -= 1
                long_or_short = -1

        if long_or_short != 0:
            return True
# @Buy limit order / user transactions
def detect_scaling_signals(context, data):
    ###
    #Place limit orders when reach scaling signals
    ###
    for sym in context.tradable_symbol:
        
        # ABS??
        if context.MT[sym]['scale-in stage'] == 0 or ABS(context.MT[sym]['scale-in stage']) == 4:
            continue
        
        current_price = data.current(context.cfutures[market], 'price') # needs to be changed
        long_or_short = 0

        previous_entry_time = retrieve_entry_time(sym, ABS(context.MT[sym]["scale-in stage"]))
        previous_entry_price = retrieve_entry_price(context, data, sym, previous_entry_time)

        if context.MT[sym]['scale-in stage'] > 0:
            if current_price - previous_entry_price > 0.5*context.MT[sym]['ATR']:

                long_or_short = 1
                context.MT[sym]['scale-in stage'] += 1


        else if context.MT[sym]['scale-in stage'] < 0:
            if previous_entry_price - current price > 0.5*context.MT[sym]['ATR']:

                long_or_short = -1
                context.MT[sym]['scale-in stage'] -= 1
        #ABS??
        if long_or_short != 0:
            entry_time = get_datetime()
            store_entry_time(sym, ABS(context.MT[sym]['scale-in stage']), entry_time)

            #chnage to HTTPS - BUY LIMIT ORDER
            return True
    
# @Sell market order
def detect_exit_signals(context, data):
