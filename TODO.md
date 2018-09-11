Todos
=====

## Strategy
- Remove Strategy.execute() training wheels. Allow user to have complete control
  over event data.
- Strategy base class expose interface through non-dunder methods instead.
  Otherwise use metaclass.

## Metric
- Metric base class keep numeric operator overloads
- Attachment to candle instance feels clumsym, consider using metaclasses

## Feed
- Create turn datafeed from module into subpackage
- Import bitfinex datafeed code
- Remove pysher dependancy with in house code
