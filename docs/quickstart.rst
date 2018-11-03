.. _quickstart:

Quickstart
==========
This document gets you started with Cryptle in 5 minutes by examples in
backtesting and step-by-step explanations.

Say one day you have the ingenious idea of buying BTC whenever it goes over
$200 and selling it whenever it's above $400. The simplest way to codify that in
plain python is::

    def winning_strategy(self, price):
        if price > 200:
            # buy
        if price < 400:
            # sell


While the function above can already fully encapsulate the business logic of our
strategy, Cryptle can only help strategies that are written as a
:class:`~cryptle.strategy.Strategy` object. Let's do exact that::

    from cryptle.strategy import SingleAssetStrat
    class BTCStrat(SingleAssetStrat):
        def winning_strategy(self, price):
            # ... same as  above


Another core mechanicism in Cryptle is the :ref:`Event Bus <events>`.

Helper functions
----------------
The `backtest module <:mod:cryptle.backtest>` has many helper functions to
backtest strategies of various types of financial data. The

::
    import json
    from cryptle.backtest import backtest_with_bus

    strat = BTCStrat()
    backtest_with_bus(strat, data)



