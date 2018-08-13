Concepts
========
manage dependency
manage messages
transfer data
store data

datafeed
strategy
place order
route order


Scenerios
=========
Common:
- strategy depends on metrics
- metrics depend on datafeed

Complex:
- Dual strategies
- Separated stratgies for trade and order placement
- Metastrategies for basket of assets

# Things that would be good to have
- declarative dependency
- single responsibility principle: require well defined flexible interface

# Flows
## Basic linear flow
datafeed -> strategy -> place order

## Common linear flow
datafeed -> metrics/models -> strategy -> place order -> route order

## Complex flow
datafeed -> metrics -> metrics -> strategy -> strategy -> place order
datafeed -> metrics -> strategy -> place order -> strategy -> place order


Problems with X
===============

# DI
Heavy opinionated framework could lead to tougher extensibiliy.
i.e. The original cryptle and pyalgotrade both directly depends on an instance
of broker through DI. While this makes sense for most strategies, it breaks down
with complicated use such as metastrats.

Usage of scripts to wrap Strats and Metrics together can get us pretty far as
far as SRP is concerned. However this will get messy quick again for complicated
usage. DI is again called for.

Do I really want to build my own DI framework for just cryptle? This would
possibily be the first in the Python eco-system, since no real option exists.
Sounds like a daunting task for me.

# MQ
