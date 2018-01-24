import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

if __name__ == '__main__':
    data = pd.read_csv('snooped-xrp.csv', header=None, names=['period',  'bollinger_threshold', 'bollinger_timeframe', 'trade_delay', 'upperatr', 'loweratr', 'final_equity', '# of trades'] )

    print(data.describe())
    print(data[data.final_equity > 11500].sort_values(by='final_equity', ascending = False))

    data.loc[:, ['final_equity']].plot()
    data.loc[:, ['bollinger_threshold']].plot()
    data.loc[:, ['bollinger_timeframe']].plot()

    plt.show()