import matplotlib.pyplot as plt

def plotCandles(candle, title=None, volume_bars=False, technicals=None, trades=None):
    # Plots a candlestick chart

    # Args:
    #   candledata: A filled Candlebar
    #   title: An optional title for the chart
    #   volume_bars: If True, plots volume bars
    #   color_function: A function which, given a row index and price series, returns a candle color.
    #   technicals: A list of additional data series to add to the chart.  Must be the same length as pricing.

    technicals = technicals or []
    trades = trades or []

    if volume_bars:
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [3,1]})
    else:
        fig, ax1 = plt.subplots(1, 1, figsize=(16,12))
        ax1.set_facecolor('0.15')

    if title:
        ax1.set_title(title)

    for i, bar in enumerate(candle):
        op = bar[0]
        cl = bar[1]
        hi = bar[2]
        lo = bar[3]

        barlen = abs(op - cl)
        bottom = min(op, cl)
        color = 'r' if op > cl else 'g'
        fill  = True if color =='r' else False

        ax1.bar(i, barlen, bottom=bottom, color=color, edgecolor=color, fill=fill, linewidth=1)
        ax1.vlines(i, lo, hi, color=color, linewidth=1)

    time_format = '%H:%M'
    xlabels = [i * int(len(candle)/7) for i in range(8)]

    # Plot buy/sells
    for trade in trades:
        color = 'g' if trade[2] == 1 else 'r'
        ax1.axvspan(trade[0], trade[1], facecolor=color, alpha=0.35)

    # Plot indicators
    for indicator in technicals:
        ax1.plot(x, indicator)

    dt = [datetime.fromtimestamp(candle[x][4] * candle.period).strftime('%H:%M') for x in xlabels]

    # Set X axis tick labels.
    plt.xticks(xlabels, dt)

    # Legacy Code, doesn't work
    if volume_bars:
        volume = candle['volume']
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

    fig.show()

