# @TODO Consider numpy for potential speed up in vectorised numeric operations

__doc__ = '''
This module provides pure generic functions that are commonly used calculating
indices and metrics related to time series. Currently avaiable functions are
mostly concerned with transforming series with rolling windows.
'''

def sma(series, lookback):
    output_len = len(series) - lookback + 1
    return [sum(x for x in series[i : i+lookback]) / lookback for i in range(output_len)]


def wma(series, lookback):
    output_len = len(series) - lookback + 1
    weight = [x + 1 / (lookback * (lookback + 1) / 2) for x in range(lookback)]
    return [sum(s * w for s, w in zip(series[i : i+lookback], weight)) for i in range(output_len)]


def ema(series, lookback):
    output_len = len(series) - lookback + 1
    weight =  2 / (lookback + 1)
    output = [series[0]]
    for i, val in enumerate(series[1:]):
        output.append(weight * val + (1 - weight) * output[-1])
    return output


def bollinger_width(series, lookback, roll_method=sma):
    output_len = len(series) - lookback + 1
    mean = roll_method(series, lookback)
    output = []
    for i in range(output_len):
        diff_square = [(x - mean[i]) ** 2 for x in series[i : i+lookback]]
        output.append((sum(diff_square) / lookback) ** 0.5)
    return output
