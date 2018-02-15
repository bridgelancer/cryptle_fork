from datetime import datetime
from colorsys import *
import matplotlib.pyplot as plt

# @Temporary wrapper for transitioning
def plotCandles(*args, **kws):
    plot(*args, **kws)


def plot(candle=None,
        title=None,
        trades=[],
        signals=[],
        indicators=[],
        plot_volume=False,
        volume_title=None,
        trade_color_mid_pt=0.025,
        fig=None):
    '''Wrapper function for OO interface of CandleStickChart

    Args:
        candledata: A filled Candlebar

        title: An optional title for the chart

        plot_volume: If True, plot volume bars

        signals: Sequence of metrics to be plotted over (on top of) the candlestick chart

        indicators: Sequence of sequence of metrics to plotted below the candlestick chart in
            subplots. The number of subplots is deteremined by len(indicators)

        trades: A list of tuples in the following format
            (entry_time, entry_price, exit_time, exit_price)
    '''
    numplots = 1 + len(indicators) + plot_volume
    chart = CandleStickChart(numplots, title)

    chart.plotCandle(candle, plot_volume)
    chart.plotTrade(trades, trade_color_mid_pt=trade_color_mid_pt)
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


    def plotCandle(self, candle, plot_volume=False, numxlabels=10):
        '''Plot green/red ochl candlesticks onto the chart

        Args:
            candle (list): Each element is a tuple with 7 elements. In the order
                (open, close, high, low, unix timestamp, volume, net volume)
            plot_volume (bool): Flag to create a volume subplot
            numxlabels (int): No. of datetime labels on the x-axis
        '''
        n = len(candle)

        barlen = [abs(bar[0] - bar[1]) for bar in candle]
        bottom = [min(bar[0], bar[1]) for bar in candle]
        hi = [bar[2] for bar in candle]
        lo = [bar[3] for bar in candle]
        ts = [bar[4] for bar in candle]

        color = ['g' if bar[0] < bar[1] else 'r' for bar in candle]
        fill  = [c == 'r' for c in color]

        self._axes[0].bar(ts, height=barlen, bottom=bottom, width=20, color=color,
                edgecolor=color, fill=fill, linewidth=1)
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
        ticks = [candle[x][4] for x in range(0, n, int(n / numxlabels))]
        dates = [datetime.fromtimestamp(t).strftime(time_format) for t in ticks]
        self._axes[0].set_xticks(ticks)
        self._axes[0].set_xticklabels(dates, rotation=30)


    def plotTrade(self, trades, trade_color_mid_pt=0.025):
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

            color = '#ffff96'

            # winning trade greater than 0.5%
            if p_and_l > 0.005:
                inv_pl = trade_color_mid_pt / (p_and_l + trade_color_mid_pt)
                h = 0.38
                s = 1 - inv_pl * 0.95
                v = 0.1 + inv_pl * 0.9
                color = hsv_to_rgb(h, s, v)

            # losing trade greater than -0.5%
            if p_and_l < -0.005:
                p_and_l *= -1
                inv_pl = trade_color_mid_pt / (p_and_l + trade_color_mid_pt)
                h = 0.998
                s = 1 - inv_pl * 0.95
                v = 0.1 + inv_pl * 0.9
                color = hsv_to_rgb(h, s, v)

            self._axes[0].axvspan(entry, exit, facecolor=color, alpha=0.4)


    def plotSignal(self, signal):
        '''Plot metrics over the candlestick chart

        Args:
            signal: A (2 x N) series; (1, :) are unix timestamps; and (2, :) are signal values
        '''
        self._axes[0].plot(signal[0], signal[1])


    # @Bad interface @Fix
    def plotIndicator(self, indicator):
        '''Plot indicators below the candlestick chart

        Args:
            indicator: A (2 x N) series; (1, :) are unix timestamps; and (2, :) are indicator values
        '''
        self._axcounter += 1
        ax = self._axes[-self._axcounter]
        for i in indicator:
            ax.plot(i[0], i[1])

    def scale(self):
        for ax in self._axes:
            ax.use_stick_edges = False
            ax.autoscale()
