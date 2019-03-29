import pytest

from cryptle.exchange.base import Order
from cryptle.exchange.base import Orderbook


CAPITAL = 100000.0
ASSET  =  'btc'
BASE   =  'usd'
PAIR   = 'btcusd'
PRICE  = 1000.0
AMOUNT = 100.0


def test_public_api():
    with pytest.raises(ImportError):
        from cryptle.exchange import Order


def test_order_attrs():
    order = Order(1, 5.0, 100.0, False, False, False, 0)
    assert order.oid == 1
    assert order.amount == 5.0
    assert order.limit_price == 100.0
    assert order.partial_filled == False
    assert order.filled == False
    assert order.cancelled == False
    assert order.filled_amount == 0


def test_limit_buy():
    book = Orderbook()

    oid = book.create_bid(AMOUNT, PRICE)
    filled, partial = book.fill_bid_by_amount(AMOUNT)

    assert partial == None
    assert filled == {oid}
    assert len(book.bid_prices) == 0
    assert len(book.ask_prices) == 0

    oid = book.create_bid(AMOUNT, PRICE)
    assert len(book.bid_prices) == 1
    assert len(book._bids) == 1

    book.delete_bid(oid)
    assert len(book.bid_prices) == 0
    assert len(book._bids) == 0


def test_limit_sell():
    book = Orderbook()

    oid = book.create_ask(AMOUNT, PRICE)
    filled, partial = book.fill_ask_by_amount(AMOUNT)

    assert partial == None
    assert filled == {oid}
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


def test_orderbook_fill():
    book = Orderbook()
    bid_id = book.create_bid(AMOUNT, PRICE - 100)
    ask_id = book.create_ask(AMOUNT, PRICE + 100)
    assert len(book.bid_prices) == 1
    assert len(book.ask_prices) == 1
    assert len(book._bids) == 1
    assert len(book._asks) == 1

    # orderbook looks| bid: 900*100, ask: 1100*100 |
    # sell comes in at 890*100, bid filled
    filled, partial = book.fill_bid(AMOUNT, PRICE - 110)

    assert filled == set((bid_id,))
    assert partial == None
    assert len(book.bid_prices) == 0
    assert len(book._bids) == 0

    # buy comes in at 1050*100, orderbook doesn't trigger fill
    book.fill_ask(AMOUNT, PRICE + 50)
    assert len(book._asks) == 1
    assert book._asks[ask_id] == (AMOUNT, PRICE + 100)

    # buy comes in at 1100*100, ask filled
    book.fill_ask(AMOUNT, PRICE + 110)
    assert len(book._asks) == 0
