import sys
import time
import json
import cryptle.logging as logging
import traceback
from threading import Thread
from collections import defaultdict

import websocket as ws

from .exception import *


logger = logging.getLogger(__name__)
KEY = 'de504dc5763aeef9ff52'
CLIENT_ID = 'PythonPusherClient'
VERSION = '0.2.0'
PORT = 80
PROTOCOL = 6


def _build_urlparams(**kwargs):
    return '&'.join('{}={}'.format(k, v) for k, v in kwargs.items())


def _build_bitstamp_url():
    query_params = _build_urlparams(
        client=CLIENT_ID, version=VERSION, protocol=PROTOCOL
    )
    url = 'ws://ws.pusherapp.com:{}/app/{}?{}'.format(PORT, KEY, query_params)
    return url


def decode_event(event):
    """Parse event string in cryptle representation into bitstamp representation."""
    channel, *params = event.split(':')
    if channel == 'trades':
        bs_chan = 'live_trades'
        bs_event = 'trade'

    elif channel == 'bookchange':
        bs_chan = 'live_orders'
        bs_event = 'order_changed'

    elif channel == 'bookcreate':
        bs_chan = 'live_orders'
        bs_event = 'order_created'

    elif channel == 'bookdelete':
        bs_chan = 'live_orders'
        bs_event = 'order_deleted'

    elif channel == 'bookdiff':
        bs_chan = 'diff_order_book'
        bs_event = 'data'

    else:
        raise BadEvent(event)

    # quickfix for stupid bitstamp legacy API
    pair = params.pop(0)
    if pair != 'btcusd':
        bs_chan += '_' + pair

    return bs_chan, bs_event, params


def encode_event(msg: dict):
    """Parse incoming websocket messages into cryptle representation."""
    channel = msg['channel']
    event = msg['event']

    # Hacky ways to decode. Very susceptible to change in bitstamp APIs
    if event == 'trade':
        if channel == 'live_trades':
            pair = 'btcusd'
        else:
            pair = channel[-6:]
        return ':'.join(('trades', pair))

    elif event == 'data' and channel[:4] == 'diff':
        if channel == 'diff_order_book':
            pair = 'btcusd'
        else:
            pair = channel[-6:]
        return ':'.join(('bookdiff', pair))
    elif event == 'data':
        if channel == 'order_book':
            pair = 'btcusd'
        else:
            pair = channel[-6:]
        # Pushed orderbooks not supported
        raise BadEvent(msg)
    else:
        if event == 'order_changed':
            evt = 'bookchange'
        elif event == 'order_created':
            evt = 'bookcreate'
        elif event == 'order_deleted':
            evt = 'bookdelete'
        else:
            raise BadEvent(msg)

        if channel == 'live_orders':
            pair = 'btcusd'
        else:
            pair = channel[-6:]

        return ':'.join((evt, pair))


def _parse_wsmsg(msg):
    return json.loads(msg)


class BitstampFeed:
    """Datafeed for bitstamp.

    Provides a javascript-like interface for various types of supported bitstamp
    events. Details are provided at https://www.bitstamp.net/websocket/
    """

    def __init__(self, *args, **kwargs):
        self._callbacks = defaultdict(list)
        self._channels = set()
        self._recv_thread = None

        self._ws = ws.WebSocket(*args, **kwargs)
        self._ws.settimeout(3)

    # ----------
    # Public interface
    # ----------
    def connect(self):
        """Connect to Bitstamp."""
        if self.connected:
            return

        logger.info('Attempting to connect')
        url = _build_bitstamp_url()
        self._ws.connect(url)
        logger.info('Connection established')

        self._recv_thread = Thread(target=self._recvForever)
        self._recv_thread.setDaemon(True)
        self.running = True
        self._recv_thread.start()

    def disconnect(self):
        """Disconnect from Bitstamp."""
        if self.connected:
            if self._recv_thread.is_alive():
                self.running = False
                self._recv_thread.join()
            self._ws.close()

    @property
    def connected(self):
        return self._ws.connected

    def on(self, event, cb):
        # Todo: Support defered callback binding
        if not self.connected:
            raise ConnectionClosed()

        if not callable(cb):
            raise TypeError('Expected 2nd argument to be callable')

        channel, *args = decode_event(event)
        if not channel in self._channels:
            self._subscribe(channel)

        self._callbacks[event].append(cb)
        try:
            # functions
            logger.info('Add callback <{}> for event "{}"', cb.__name__, event)
        except AttributeError:
            # functors
            logger.info('Add callback {} for event "{}"', repr(cb), event)

    # ----------
    # Outgoing messages complying to Pusher API
    # ----------
    def _subscribe(self, channel):
        logger.info('Subscribing to channel: {}', channel)
        self._send({'event': 'pusher:subscribe', 'data': {'channel': channel}})

    def _unsubscribe(self, channel):
        logger.info('Unsubscribing from channel: {}', channel)
        self._send({'event': 'pusher:unsubscribe', 'data': {'channel': channel}})

    def _pong(self):
        logger.info('Ping-pong')
        self._send({'event': 'pusher:pong'})

    def _send(self, msg):
        """Low level method to send a websocket message.

        Args:
            msg: A python tuple/list/dict representing the message.
        """
        raw_msg = json.dumps(msg)
        self._ws.send(raw_msg)
        logger.debug('Sent: {}', raw_msg)

    # ----------
    # Process incoming messages
    # ----------
    def _recvForever(self):
        """Main loop to receive incoming socket messages.

        Messages are received using the blocking WebSocket.recv() method. The
        raw string messages are then parsed into python objects and passed onto
        the appropriate methods for the corresponding types of message.
        """
        logger.info('Receiver thread started')
        while self.connected and self.running:
            try:
                # Recevive low level websocket message
                try:
                    raw_msg = self._ws.recv()
                except ws.WebSocketConnectionClosedException:
                    # Todo: restart?
                    logger.warning('Websocket closed')
                    break
                except ws.WebSocketTimeoutException:
                    continue

                # Process messsage according to pusher API
                msg = _parse_wsmsg(raw_msg)
                event = msg['event']
                data = msg['data']

                if event == 'pusher:connection_established':
                    # Todo: handle protocol version 7 timeout parameter
                    continue
                elif event == 'pusher_internal:subscription_succeeded':
                    # Todo: improve subscription tracking
                    continue
                elif event == 'pusher:ping':
                    self._pong()
                elif event == 'pusher:pong':
                    self._pong()
                else:
                    cryptle_event = encode_event(msg)
                    for cb in self._callbacks[cryptle_event]:
                        # Double JSON decode because Bitstamp/Pusher is stupid
                        # Pusher recommends double encoded JSON, and Bitstamp followed
                        cb(json.loads(data))

            except Exception as e:
                _, _, tb = sys.exc_info()
                traceback.print_tb(tb)
                logger.error('(callback error):{}({})', type(e).__name__, e)

            else:
                logger.debug('Received: {}', raw_msg)
