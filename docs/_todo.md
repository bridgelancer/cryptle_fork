Todo
====

## Strategy
- Remove Strategy.execute() training wheels. Allow user to have complete control
  over event data.
- Strategy base class expose interface through non-dunder methods instead.
  Otherwise use metaclass.

## Metric
- Metric base class keep numeric operator overloads
- Attachment to candle instance feels clumsym, consider using metaclasses
