from cryptle.exchange.paper import Orderbook, Paper


CAPTIAL = 100000.0
PAIR   = 'btcusd'
PRICE  = 1000.0
AMOUNT = 100.0


def test_limit_buy():
    book = Orderbook()
    book.create_bid(AMOUNT, PRICE)
    book.take_bid(AMOUNT, PRICE)


def test_limit_buy_with_id():
    book = Orderbook()
    oid = book.create_bid(AMOUNT, PRICE)
    book.take_bid_with_id(oid)


def test_limit_sell():
    book = Orderbook()
    book.create_ask(AMOUNT, PRICE)
    book.take_ask(AMOUNT, PRICE)


def test_limit_sell_with_id():
    book = Orderbook()
    oid = book.create_ask(AMOUNT, PRICE)
    book.take_ask_with_id(oid)


def test_paper_market_order():
    paper = Paper(CAPTIAL)
    paper.update(PAIR, PRICE)

    paper.marketBuy(PAIR, AMOUNT)
    assert paper.capital == CAPTIAL - PRICE * AMOUNT
    paper.marketSell(PAIR, AMOUNT)
    assert paper.capital == CAPTIAL
