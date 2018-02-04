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
