from datetime import datetime

import matplotlib.pyplot as plt

def plotCandles(candle, title=None, technicals=None, trades=None, plot_volume=False, volume_title=None,
        volume_):
    # Args:
    #   candledata:
    #       A filled Candlebar
    #
    #   title:
    #       An optional title for the chart
    #
    #   plot_volume:
    #       If True, plots volume bars
    #
    #   color_function:
    #       A function which, given a row index and price series, returns a candle color.
    #
    #   technicals:
    #       A list of additional data series to add to the chart.  Must be the same length as pricing.
    #
    #   trades:
    #       A list of tuples in the format (entry_time, entry_price, exit_time, exit_price)
    #       the entry and exit times should be in unix timestamp

    technicals = technicals or []
    trades = trades or []

    if plot_volume:
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [3,1]})
    else:
        fig, ax1 = plt.subplots(1, 1, figsize=(16,12))

    if title:
        ax1.set_title(title)


    # Plot the bars and lines through bars
    for i, bar in enumerate(candle):
        op = bar[0] # open
        cl = bar[1] # close
        hi = bar[2] # hi
        lo = bar[3] # low

        barlen = abs(op - cl)
        bottom = min(op, cl)
        color = 'r' if op > cl else 'g'
        fill  = True if color =='r' else False

        ax1.bar(i, barlen, bottom=bottom, color=color, edgecolor=color, fill=fill, linewidth=1)
        ax1.vlines(i, lo, hi, color=color, linewidth=1)

    # Plot buy/sells
    for trade in trades:
        try:
            entry = int(trade[0]) # entry time (buy)
            exit  = int(trade[2]) # exit time (sell)

            # find the corresponding candle where the buy/sell happened
            entry_bar = int((entry - candle[0][4] * candle.period) / candle.period)
            exit_bar  = int((exit  - candle[0][4] * candle.period) / candle.period)

            p_and_l = (trade[3] - trade[1])/trade[1]

        except IndexError:
            # when the strategy terminated without selling (still holding a position)
            entry = int(trade[0])

            exit_bar  = len(candle)
            entry_bar = int((entry - candle[0][4] * candle.period) / candle.period)

            p_and_l = (candle.last - trade[1])/trade[1]

        # winning trade colors
        if p_and_l > 0.005:
            color = '#97ED8A'
        if p_and_l > 0.01:
            color = '#45BF55'
        if p_and_l > 0.015:
            color = '#167F39'
        if p_and_l > 0.02:
            color = '#044C29'

        # winning trade colors
        if p_and_l < -0.005:
            color = '#D40D12'
        if p_and_l < -0.01:
            color = '#94090D'
        if p_and_l < -0.015:
            color = '#5C0002'
        if p_and_l < -0.02:
            color = '#450003'

        ax1.axvspan(entry_bar, exit_bar, facecolor=color, alpha=0.35)

    # Plot indicators
    for indicator in technicals:
        ax1.plot(x, indicator)

    # Plots volume
    if plot_volume:
        volume = [x[5] for x in candle.bars]
        volume_scale = None
        scaled_volume = volume
        if volume.max() > 1000000:
            volume_scale = 'M'
            scaled_volume = volume / 1000000
        elif volume.max() > 1000:
            volume_scale = 'K'
            scaled_volume = volume / 1000
        ax2.bar(x, scaled_volume, color=candle_colors)
        volume_title = 'Volume'
        if volume_scale:
            volume_title = 'Volume (%s)' % volume_scale
        ax2.set_title(volume_title)
        ax2.xaxis.grid(False)


    # Set X axis tick labels.
    time_format = '%m-%d %H:%M'

    xlabels = [i * int(len(candle)/7.5) for i in range(8)]
    dt = [datetime.fromtimestamp(candle[x][4] * candle.period).strftime('%H:%M') for x in xlabels]
    plt.xticks(xlabels, dt)

    return fig
