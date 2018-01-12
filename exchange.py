import logging


log = logging.getLogger('Exchange')


class PaperExchange:

    def marketBuy(self, pair, amount):
        assert isinstance(pair, str)
        assert amount > 0

        log.info('Buy  {:>7.2f} {} @${:.2}'.format(amount, pair.upper(), price))
        return {'price': price, 'amount': amount}


    def marketSell(self, pair, amount):
        assert isinstance(pair, str)
        assert amount > 0

        log.info('Sell {:>7.2f} {} @${:.2f}'.format(amount, pair.upper(), price))
        return {'price': price, 'amount': amount}

    def limitBuy(self, pair, amount, price):
        assert isinstance(pair, str)
        assert amount > 0
        assert price > 0

        log.info('Buy  {:>7.2f} {} @${:.2}'.format(amount, pair.upper(), price))
        return {'price': price, 'amount': amount}


    def limitSell(self, pair, amount, price):
        assert isinstance(pair, str)
        assert amount > 0
        assert price > 0

        log.info('Sell {:>7.2f} {} @${:.2f}'.format(amount, pair.upper(), price))
        return {'price': price, 'amount': amount}


