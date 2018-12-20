import os
import csv

this_dir, _ = os.path.split(__file__)

TRADE_FILE = os.path.join(this_dir, 'sample_trades.csv')
CANDLE_FILE = os.path.join(this_dir, 'sample_candles.csv')


def get_sample_trades(name=TRADE_FILE):
    return load_csv(name)


def get_sample_candles(name=CANDLE_FILE):
    return load_csv(name)


def load_csv(name):
    """Load csv into memory."""
    with open(name) as f:
        reader = csv.reader(f)
        sniffer = csv.Sniffer()

        # skip the header row
        if sniffer.has_header(open(name, newline='').read(1024)):
            reader.__next__()

        return [r for r in reader]
