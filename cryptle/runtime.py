import pprint
import sys
import time
import threading


class Runtime:
    """Live execution environment for strategies.

    This class provides an interface to query runtime information of a strategy.
    Updates are also performed through querying an exchange. All read/write is
    done through the Unix stdio.

    This class can act as base for more specialized I/O sources. Subclasses may
    read from any inputs and write to any outputs by overwriting the methods:
    - run_forever()
    - read_command_forever()
    - handle_input()
    """
    help_str = (
        '\n'
        'h | help           Print this help\n'
        'r | report         Report current portfolio status\n'
        'l | list           List available strategy attributes\n'
        'q | quit | exit    Terminate runtime\n'
        '<attribute>        Print the value of <attribute>\n'
    )

    def __init__(self,
            strat,
            exchange,
            reporting_time=60,
            interval=1):

        self.strat = strat
        self.port = strat.portfolio
        self.exchange = exchange
        self.reporting_time = reporting_time
        self.interval = interval
        self._terminated = False

        self.asset = self.strat.asset
        self.base_currency = self.strat.base_currency

    def run_forever(self):
        """Start the reporting thread and run forever."""
        report_thread = threading.Thread(target=self._report_loop)
        report_thread.start()
        print(self.help_str)
        self.report()
        self.read_command_forever()

    def read_command_forever(self, stream=sys.stdin):
        """Read and process an input stream as commands forever.

        Since the default stream is sys.stdin, this method does not attempt to
        close the provided stream.
        """
        try:
            for line in stream:
                if line:
                    s = self.handle_input(line)
        except KeyboardInterrupt:
            print('Received termination request')
        except Exception as e:
            print('Caught unhandled exception {}'.format(e))
        finally:
            print('Terminating main loop...')
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
                    self.report()
            except:
                # @Incomplete: Handle connection issues
                pass


    def handle_input(self, line):
        s = self.process_command(line)
        print(s)


    def process_command(self, line):
        """Return a string result after processing the commaned"""
        line = line.strip()

        if line == 'h' or line == 'help':
            return self.help_str
        elif line == 'r' or line == 'report':
            return self._get_report_str()
        elif line == 'l' or line == 'list':
            # @Incomplete: Put last square bracket on new line
            return pprint.pformat(list(self.strat.__dict__.keys()), indent=4)
        elif line == 'q' or line == 'quit' or line == 'exit':
            raise KeyboardInterrupt
        else:
            # @Refactor: Wrap try around the conditional, return better message
            try:
                return self.strat.__dict__[line]
            except KeyError:
                return 'Attribute does not exist'


    def report(self):
        print(self._get_report_str())


    def _get_report_str(self):
        s = (
            'Equity:  {}\n'
            'Cash:    {}\n'
            'Balance: {}\n'
        )
        p = self.port
        return s.format(p.equity, p.cash, p.balance)


    def _get_help_str(self):
        return self.help_str
