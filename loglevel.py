import logging

# CRITICAL = 50
# ERROR    = 40
# WARNING  = 30
# INFO     = 20
# DEBUG    = 10
# NOTSET   = 0

logging.TICK    = 9
logging.TA      = 9
logging.REPORT  = 21

logging.addLevelName(logging.TICK, 'TICK')
logging.addLevelName(logging.TA, 'TA')
logging.addLevelName(logging.REPORT, 'REPORT')

