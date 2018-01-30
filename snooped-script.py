import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

if __name__ == '__main__':
    data = pd.read_csv('snoop-bch.csv', header=None, names=['period',  'bband', 'bollinger_timeframe', 'trade_delay', 'upperatr', 'loweratr', 'bband_lookback', 'not used', 'final_equity', '# of trades'] )

    print(data.describe())
    print(data[(data.bband < 6) & (data.bband >= 4)].final_equity.describe())
    print(data[(data.bband < 8) & (data.bband >= 6)].final_equity.describe())
    print(data[(data.bband < 10) & (data.bband >= 8)].final_equity.describe())
    print(data[(data.bband <= 12) & (data.bband >= 10)].final_equity.describe())

    print(data[data.final_equity > 10000].sort_values(by='final_equity', ascending = False))

    data.loc[:, ['final_equity']].plot()
    data.loc[:, ['bband']].plot()
    data.loc[:, ['bollinger_timeframe']].plot()

    plt.show()