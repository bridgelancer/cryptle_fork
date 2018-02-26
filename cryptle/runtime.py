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
            reporting_time=60,
            interval=1,
            istream=sys.stdin,
            ostream=print):

        self.strat = strat
        self.port = strat.portfolio
        self.exchange = exchange
        self.reporting_time = reporting_time
        self.interval = interval
        self._input = istream
        self._output = ostream
        self._terminated = False

        self.asset = self.strat.asset
        self.base_currency = self.strat.base_currency



    def run_forever(self):
        report_thread = threading.Thread(target=self._report_loop)
        report_thread.start()

        self._output(self.help_text)
        self._report()

        try:
            for line in self._input:
                if line:
                    s = self._handle_input(line)
                    self._output(s)
        except KeyboardInterrupt:
            self._output('Received termination request')
        except Exception as e:
            self._output('Caught unhandled exception {}'.format(e))
        finally:
            self._output('Terminating main loop...')
            self._terminated = True


    def _report_loop(self):
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


    def _handle_input(self, line):
        '''Return string result of processed commaned'''

        line = line.strip()

        if line == 'h':
            return self.help_text
        elif line == 'r':
            p = self.port
            self._report()
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


    def _report(self):
        self._output(self._get_report_string())


    def _get_report_string(self):
        s = (
            'Equity:  {}\n'
            'Cash:    {}\n'
            'Balance: {}\n'
        )
        s.format(self.port.equity, self.port.cash, self.port.balance)
        return s
