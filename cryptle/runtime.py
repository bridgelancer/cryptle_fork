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

        self.terminated = False
        self.strat = strat
        self.port = strat.portfolio
        self.exchange = exchange
        self.log = logger
        self.reporting_time = reporting_time
        self.interval = interval
        self.input = istream
        self.output = ostream
        self.terminated = False

        self.asset = self.strat.asset
        self.base_currency = self.strat.base_currency


    def handle_input(self, line):
        '''Handle commands. Return string representation command result'''
        line = line.strip()

        if line == 'h':
            return self.help_text

        elif line == 'r':
            p = self.port
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
        while not self.terminated:
            time.sleep(self.interval)
            s += self.interval
            s %= self.reporting_time

            # Hardcoded for bitstamp
            prices = {self.asset: float(self.exchange.getTicker(self.asset, self.base_currency)['last'])}
            balance = self.exchange.getBalance()

            if s == 0:
                #if new_balance_value != port.balance_value:
                self.log_report()

            else:
                # @Dependence on Bitstamp API
                pass

    def init(self):
        self.output(help_text)
        self.log.debug('Reporting started')
        self.log_report()


    def log_report(self):
            self.log.report('Equity:  {}'.format(self.port.equity))
            self.log.report('Cash:    {}'.format(self.port.cash))
            self.log.report('Balance: {}'.format(self.port.balance))


    def run_forever(self):
        report_thread = threading.Thread(target=self.report_loop)
        report_thread.start()

        try:
            for line in self.input:
                if line:
                    s = self.handle_input(line)
                    self.output(s)
        except KeyboardInterrupt:
            self.output('Received termination request')
        except Exception as e:
            self.output('Caught unhandled exception {}'.format(e))
        finally:
            self.output('Terminating main loop...')
            self.terminated = True
