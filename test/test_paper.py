import pytest

from cryptle.exchange.paper import Orderbook, Paper


CAPTIAL = 100000.0
PAIR   = 'btcusd'
PRICE  = 1000.0
AMOUNT = 100.0


def test_limit_buy():
    book = Orderbook()

    oid = book.create_bid(AMOUNT, PRICE)
    filled, partial = book.take_bid(AMOUNT)

    assert partial == (None, None)
    assert filled == {oid}
    assert len(book.bid_prices) == 0
    assert len(book.ask_prices) == 0

    oid = book.create_bid(AMOUNT, PRICE)
    book.delete_bid(oid)

    assert len(book.bid_prices) == 0
    assert len(book.ask_prices) == 0


def test_limit_sell():
    book = Orderbook()

    book.create_ask(AMOUNT, PRICE)
    book.take_ask(AMOUNT)

    oid = book.create_ask(AMOUNT, PRICE)
    book.delete_ask(oid)

    assert len(book.bid_prices) == 0
    assert len(book.ask_prices) == 0


def test_orderbook_raise_on_invalid_create():
    book = Orderbook()
    book.create_bid(AMOUNT, PRICE - 100)
    book.create_ask(AMOUNT, PRICE + 100)

    with pytest.raises(ValueError):
        book.create_bid(AMOUNT, PRICE + 200)

    with pytest.raises(ValueError):
        book.create_ask(AMOUNT, PRICE - 200)


def test_paper_market_order():
    paper = Paper(CAPTIAL)
    paper.update(PAIR, PRICE)

    paper.marketBuy(PAIR, AMOUNT)
    assert paper.capital == CAPTIAL - PRICE * AMOUNT
    paper.marketSell(PAIR, AMOUNT)
    assert paper.capital == CAPTIAL
