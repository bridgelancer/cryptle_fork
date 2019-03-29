import pytest

from cryptle.exchange import Paper
from cryptle.exchange.base import Orderbook


CAPITAL = 100000.0
ASSET  =  'btc'
BASE   =  'usd'
PAIR   = 'btcusd'
PRICE  = 1000.0
AMOUNT = 100.0


def test_keep_track_of_market_price():
    paper = Paper(CAPITAL)
    paper.updatePrice(PAIR, PRICE)
    assert paper._last_price[PAIR] == PRICE

    paper.update(PAIR, AMOUNT, PRICE)
    assert paper._last_price[PAIR] == PRICE


def test_paper_market_order():
    paper = Paper(CAPITAL)
    paper.update(PAIR, AMOUNT, PRICE)

    paper.marketBuy(ASSET, BASE, AMOUNT)
    assert paper.capital == CAPITAL - PRICE * AMOUNT
    paper.marketSell(ASSET, BASE, AMOUNT)
    assert paper.capital == CAPITAL


def test_paper_limit_order():
    paper = Paper(CAPITAL)
    paper.update(PAIR, AMOUNT, PRICE)
    book = paper._orderbooks[PAIR]

    success, oid = paper.limitBuy(ASSET, BASE, AMOUNT, PRICE - 100)
    assert success

    success, oid= paper.limitSell(ASSET, BASE, AMOUNT, PRICE + 100)
    assert success

    assert paper.capital == CAPITAL
    assert len(book._bids) == 1
    assert len(book._asks) == 1

    paper.update(PAIR, AMOUNT, PRICE - 110)  # buy
    assert len(book._bids) == 0
    assert len(book._asks) == 1

    paper.update(PAIR, AMOUNT, PRICE + 110)  # sell
    assert len(book._bids) == 0
    assert len(book._asks) == 0
