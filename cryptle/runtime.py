import pprint
import time
import threading
import sys


class Runtime:
    '''Execution device for strategy, providing online diagnostics through CLI.'''

    help_text = (
        '\n'
        'Cryptle live trade\n'
        'h                  Print this help\n'
        'r                  Report current portfolio status\n'
        'l                  List available strategy attributes\n'
        'q | quit | exit    Terminate runtime\n'
        '<attribute>        Print the value of <attribute>\n'
    )

    def __init__(self,
            strat,
            exchange,
            logger,
            reporting_time=60,
            interval=1,
            istream=sys.stdin,
            ostream=print):

        self.strat = strat
        self.port = strat.portfolio
        self.exchange = exchange
        self.logger = logger
        self.reporting_time = reporting_time
        self.interval = interval
        self._input = istream
        self._output = ostream
        self._terminated = False

        self.asset = self.strat.asset
        self.base_currency = self.strat.base_currency


    def handle_input(self, line):
        '''Handle commands. Return string representation command result'''
        line = line.strip()

        if line == 'h':
            return self.help_text
        elif line == 'r':
            p = self.port
            self._report()
            s = (
                'Equity:  {}\n'
                'Cash:    {}\n'
                'Balance: {}\n'
            )
            return s.format(p.equity, p.cash, p.balance)
        elif line == 'l':
            return pprint.pformat(list(self.strat.__dict__.keys()), indent=4)
        elif line == 'q' or line == 'quit' or line == 'exit':
            raise KeyboardInterrupt
        else:
            try:
                return self.strat.__dict__[line]
            except KeyError:
                return 'Attribute does not exist'


    def report_loop(self):
        s = 0
        while not self._terminated:
            time.sleep(self.interval)
            s += self.interval
            s %= self.reporting_time
            try:
                # @Hardcode: only work for bitstamp
                price = self.strat.last_price
                balance = self.exchange.getBalance()
                if s == 0:
                    # @Incomplete: report only when the balance has changed
                    self._report()
            except:
                # @Incomplete: Handle connection issues
                pass


    def init(self):
        self._output(help_text)
        self.logger.debug('Reporting started')
        self._report()


    def run_forever(self):
        report_thread = threading.Thread(target=self.report_loop)
        report_thread.start()
        try:
            for line in self._input:
                if line:
                    s = self.handle_input(line)
                    self._output(s)
        except KeyboardInterrupt:
            self._output('Received termination request')
        except Exception as e:
            self._output('Caught unhandled exception {}'.format(e))
        finally:
            self._output('Terminating main loop...')
            self._terminated = True


    def _report(self):
            self.logger.report('Equity:  {}'.format(self.port.equity))
            self.logger.report('Cash:    {}'.format(self.port.cash))
            self.logger.report('Balance: {}'.format(self.port.balance))
