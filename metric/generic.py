import numpy as np
import math

__doc__ = '''
This module provides pure generic functions that are commonly used calculating
indices and metrics related to time series. Currently avaiable functions are
mostly concerned with transforming series with rolling windows.
'''

def simple_moving_average(series, lookback):
    '''Simple Moving Average'''
    output_len = len(series) - lookback + 1
    return [sum(x for x in series[i : i+lookback]) / lookback for i in range(output_len)]


def weighted_moving_average(series, lookback):
    '''Weighted Moving Average'''
    output_len = len(series) - lookback + 1
    weight = [(x + 1) / (lookback * (lookback + 1) / 2) for x in range(lookback)]
    return [sum(s * w for s, w in zip(series[i : i+lookback], weight)) for i in range(output_len)]


def exponential_moving_average(series, lookback):
    '''Exponentail Moving Average'''
    output_len = len(series) - lookback + 1
    weight =  2 / (lookback + 1)
    output = [series[0]]
    for i, val in enumerate(series[1:]):
        output.append(weight * val + (1 - weight) * output[-1])
    return output


def bollinger_width(series, lookback, roll_method=simple_moving_average):
    '''Bollinger Band bandwidth experssed in absolute value'''
    output_len = len(series) - lookback + 1
    mean = roll_method(series, lookback)
    output = []
    for i in range(output_len):
        diff_square = [(x - mean[i]) ** 2 for x in series[i : i+lookback]]
        output.append((sum(diff_square) / lookback) ** 0.5)
    return output


def bollinger_band(series, lookback, sd=2, roll_method=simple_moving_average):
    '''Bollinger Band bandwidth in percentage'''
    output_len = len(series) - lookback + 1
    up = bollinger_up(series, lookback, sd)
    low = bollinger_low(series, lookback, sd)
    output = []
    for i in range(output_len):
        output.append(((up[i] / low[i]) - 1) * 100)
    return output


def bollinger_up(series, lookback, sd= 2, roll_method=simple_moving_average):
    '''Bollinger Band upperband'''
    output_len = len(series) - lookback + 1
    width = bollinger_width(series, lookback)
    mean = roll_method(series, lookback)
    output = []
    for i in range(output_len):
        output.append(series[i + lookback - 1] + sd* width[i])
    return output


def bollinger_low(series, lookback, sd=2, roll_method=simple_moving_average):
    '''Bollinger Band lowerband'''
    output_len = len(series) - lookback + 1
    width = bollinger_width(series, lookback)
    mean = roll_method(series, lookback)
    output = []
    for i in range(output_len):
        output.append(series[i + lookback - 1] - sd* width[i])
    return output


def macd(series, fast, slow, signal, roll_method=weighted_moving_average):
    '''Moving Average Convergence Divergence'''
    fast_ma = roll_method(series, fast)
    slow_ma = roll_method(series, slow)
    fast_ma = fast_ma[slow - fast:]
    diff = [f - s for f, s in zip(fast_ma, slow_ma)]

    output = roll_method(diff, signal)

    return output


def pelt(series, cost_template, penality=None):
    '''Pruned Exact Linear Time method

    Args:
        cost: Cost function with

    Returns:
        List of changepoints in the provided data series

    Naming Convention:
        tau: A changepoint (candidate)
        F[t]: Optimal value of cost at time t
        R[t]: Pruned changepoints at time t
        cps: Unpruned changepoints at time t
    '''

    cost = cost_template(series)

    # Prepend series with a dummy entry for easier indexing
    series = [None] + series
    n = len(series)
    penality = penality or np.log(n)

    F = [-penality]
    R = [0]
    cps = [[]]

    for t in range(1, n):
        # Step 1, 2
        # Try introducing changpoint at tau: 0 < tau < t, determine the new
        # minimum cost and the tau changepoint that gave this new cost

        F_buffer = {tau : F[tau] + cost(tau+1, t) + penality for tau in R}
        t_min, F_min =  min(F_buffer.items(), key=lambda k: k[1])
        F.append(F_min)

        # Step 3, 4
        # Record the optimal set of changepoints at point of view of time t
        # Prune the remaining possible changepoints for future T > t

        cps.append(cps[t_min] + [t_min])
        R = [tau for tau in R if (F[tau] + cost(tau+1, t)) < F_min] + [t]

    return cps[-1]


def cost_normal_var(series, mean=0):
    data = np.array(series)
    cumm = np.cumsum((data - mean) ** 2)
    cumm = np.insert(cumm, 0, 0)

    def cost(start, end):
        if start == end:
            return 0
        dist = float(end - start)
        diff = cumm[end] - cumm[start]
        return dist * np.log(diff/dist)

    return cost
