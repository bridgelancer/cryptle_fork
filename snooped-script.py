import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

if __name__ == '__main__':
    data = pd.read_csv(snooped-bch.log, header=None, names=['period',  'bollinger_threshold', 'bollinger_timeframe', 'trade_delay', 'upperatr', 'loweratr', 'bollinger_lookback', 'final_equity'] )

    data.