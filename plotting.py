from datetime import datetime
import matplotlib.pyplot as plt

# @Temporary wrapper for transitioning
def plotCandles(*args, **kws):
    plot(*args, **kws)


def plot(candle=None,
        title=None,
        trades=None,
        signals=[],
        indicators=[],
        plot_volume=False,
        volume_title=None,
        fig=None):
    '''Wrapper function for OO interface of CandleStickChart

    Args:
        candledata: A filled Candlebar
        title: An optional title for the chart
        signals: Sequence of metrics to be plotted over (on top of) the candlestick chart
        indicators: Sequence of metrics to plotted below the candlestick chart in subplots
        trades: A list of tuples in the following format
            (entry_time, entry_price, exit_time, exit_price)
        plot_volume: If True, plot volume bars
    '''
    numplots = 1 + len(signals) + len(indicators) + plot_volume
    chart = CandleStickChart(numplots, title)

    chart.plotCandle(candle, plot_volume)
    chart.plotTrade(trades)
    for sign in signals:
        chart.plotSignal(sign)
    for index in indicators:
        chart.plotIndicator(index)

    chart.scale()

    return chart


class CandleStickChart:

    def __init__(self, numplots=1, title=None):
        self._fig , self._axes = plt.subplots(numplots, 1, sharex=True, figsize=(16,12))
        if numplots == 1:
            self._axes = [self._axes]

        self._axes[0].set_title(title or 'Plot')
        self._axes[0].autoscale(enable=False, axis='both')
        self._axes[0].use_stick_edges = False
        self._axcounter = 0


    # @Refactor Use Candle class interface?
    def plotCandle(self, candle, plot_volume=False, numxlabels=10):
        n = len(candle)

        barlen = [abs(bar[0] - bar[1]) for bar in candle]
        bottom = [min(bar[0], bar[1]) for bar in candle]
        hi = [bar[2] for bar in candle]
        lo = [bar[3] for bar in candle]
        ts = [bar[4] * candle.period for bar in candle]

        color = ['g' if bar[0] < bar[1] else 'r' for bar in candle]
        fill  = [c == 'r' for c in color]

        self._axes[0].bar(x=ts, height=barlen, bottom=bottom, color=color, edgecolor=color, fill=fill, linewidth=1)
        self._axes[0].vlines(x=ts, ymin=lo, ymax=hi, color=color, linewidth=1)

        # Plots volume
        if plot_volume:
            volume = [x[5] for x in candle.bars]
            self._axes[1].bar(x, volume, color=candle_colors)
            volume_title = 'Volume'
            self._axes[1].set_title(volume_title)
            self._axes[1].xaxis.grid(False)

        # Set X axis tick labels
        time_format = '%m-%d %H:%M'

        # Candle timestamps were used as x-axis labels
        ticks = [candle[x][4] * candle.period for x in range(0, n, int(n / numxlabels))]
        dates = [datetime.fromtimestamp(t).strftime(time_format) for t in ticks]
        self._axes[0].set_xticks(ticks)
        self._axes[0].set_xticklabels(dates, rotation=30)


    def plotTrade(self, trades):
        for trade in trades:
            try:
                entry = int(trade[0]) # entry time (buy)
                exit  = int(trade[2]) # exit time (sell)
                p_and_l = (trade[3] - trade[1])/trade[1]

            except IndexError:
                # when the strategy terminated without selling (still holding a position)
                entry = int(trade[0])
                exit = self._axes[0].get_xbound()[1]
                p_and_l = 0

            color = '#ffffad'

            # winning trade colors
            if p_and_l > 0.005:
                color = '#97ED8A'
            if p_and_l > 0.01:
                color = '#45BF55'
            if p_and_l > 0.015:
                color = '#167F39'
            if p_and_l > 0.02:
                color = '#044C29'

            # losing trade colors
            if p_and_l < -0.005:
                color = '#D40D12'
            if p_and_l < -0.01:
                color = '#94090D'
            if p_and_l < -0.015:
                color = '#5C0002'
            if p_and_l < -0.02:
                color = '#450003'

            self._axes[0].axvspan(entry, exit, facecolor=color, alpha=0.35)


    def plotSignal(self, signal):
        '''Plot metrics over the candlestick chart

        Args:
            signal: A (2 x N) series; (1, :) are signal values; and (2, :) are unix timestamps
        '''
        self._axes[0].plot(signal)


    def plotIndicator(self, indicators):
        '''Plot indicators below the candlestick chart

        Args:
            signal: A (2 x N) series; (1, :) are indicator values; and (2, :) are unix timestamps
        '''
        self._axcounter += 1
        ax = self._axes[-self._axcounter]
        ax.plot(indicator)

    def scale(self):
        for ax in self._axes:
            ax.use_stick_edges = True
            ax.autoscale()
