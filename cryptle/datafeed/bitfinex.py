import os
import sys
import json
import time
import socket
import logging
import traceback
from enum import Enum
from threading import Thread

import websocket as ws

from .exception import *


logger = logging.getLogger(__name__)
WSURL = 'wss://api.bitfinex.com/ws/2'


def decode_event(event):
    """Parse event string in cryptle representation into bitfinex dict representation."""
    channel, *params = event.split(':')
    kwargs = {}

    # @Todo: Implement all events
    if channel == 'trades':
        kwargs['symbol'] = params[0]
    elif channel == 'ticker':
        pass
    elif channel == 'book':
        pass
    elif channel == 'rawbook':
        pass
    elif channel == 'candles':
        symbol = params[0]
        period = params[1]
        kwargs['key'] = 'trade:{}:{}'.format(symbol, period)
    else:
        raise BadEvent(event)

    return channel, kwargs


def encode_event(msg: dict):
    """Parse subscribed messages from bitfinex into cryptle representation."""
    name = msg['channel']
    cid = msg['chanId']
    event = ''

    # @Todo: Implement all events
    if name == 'trades':
        symbol = msg['symbol'][1:].lower()
        event = 'trades:{}'.format(symbol)

    elif name == 'ticker':
        raise NotImplementedError

    elif name == 'book':
        raise NotImplementedError

    elif name == 'rawbook':
        raise NotImplementedError

    elif name == 'candles':
        _, symbol, period = msg['key'].split(':')
        event = 'candles:{}:{}'.format(symbol, period)

    return cid, event


def _parse_wsmsg(msg):
    return json.loads(msg)


class Code(Enum):
    ERR_UNK = 10000
    ERR_GENERIC = 10001
    ERR_CONCURRENCY = 10008
    ERR_PARAMS = 10020
    ERR_CONF_FAIL = 10050
    ERR_AUTH_FAIL = 10100
    ERR_AUTH_PAYLOAD = 10111
    ERR_AUTH_SIG = 10112
    ERR_AUTH_HMAC = 10113
    ERR_AUTH_NONCE = 10114
    ERR_UNAUTH_FAIL = 10200
    ERR_SUB_FAIL = 10300
    ERR_SUB_MULTI = 10301
    ERR_UNSUB_FAIL = 10400
    ERR_READY = 11000
    EVT_STOP = 20051
    EVT_RESYNC_START = 20060
    EVT_RESYNC_STOP = 20061
    EVT_INFO = 5000


class BitfinexFeed:
    """Websocket datafeed for Bitfinex.

    Attributes:
        connected: Connection status.
    """

    def __init__(self, *args, **kwargs):
        # { Channel_ID: event, ... }
        self._id_event = {}

        # { event: [cb0, cb1, ...], ... }
        self._callbacks = {}

        # Incoming messages processing thread
        self._recv_thread = None

        self._ws = ws.WebSocket(*args, **kwargs)
        self._ws.settimeout(3)

    # ----------
    # Public interface
    # ----------
    def connect(self, **options):
        """Connect to Bitfinex push data."""
        if self.connected:
            return

        logger.info('Attempting to connect')
        self._ws.connect(WSURL, **options)
        logger.info('Connection established')

        self._recv_thread = Thread(target=self._recvForever)
        self._recv_thread.setDaemon(True)
        self.running = True
        self._recv_thread.start()

    def disconnect(self):
        """Disconnect from Bitfinex."""
        if self.connected:
            if self._recv_thread.is_alive():
                self.running = False
                self._recv_thread.join()
            self._ws.close()

    @property
    def connected(self):
        return self._ws.connected

    def on(self, event, callback):
        """Bind a callback to an event.

        Args:
            event: The event to listen for.
            callback: The callback function to be binded.
        """
        if not self.connected:
            raise ConnectionClosed()

        if event not in self._callbacks:
            self._callbacks[event] = []
            channel, kwargs = decode_event(event)
            msg = {'event': 'subscribe', 'channel': channel}
            msg.update(kwargs)

            logger.info('Subscribing: {}', event)
            self._send(msg)

        self._callbacks[event].append(callback)
        logger.info('Add callback: "{}"', event)

    # ----------
    # Send outgoing messages
    # ----------
    def _send(self, msg):
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
                try:
                    raw_msg = self._ws.recv()
                except ws.WebSocketConnectionClosedException:
                    # @Todo: restart?
                    logger.warning('Websocket closed')
                    break
                except ws.WebSocketTimeoutException:
                    continue
                else:
                    wsmsg = _parse_wsmsg(raw_msg)
                    if isinstance(wsmsg, dict):
                        self._handleMessage(wsmsg)
                    elif isinstance(wsmsg, list):
                        self._handleUpdate(wsmsg)

            except Exception as e:
                _, _, tb = sys.exc_info()
                traceback.print_tb(tb)
                logger.error('(callback error):{}:{}', type(e).__name__, e)

            else:
                logger.debug('Received: {}', raw_msg)

    def _handleMessage(self, msg):
        bfx_event = msg['event']

        if bfx_event == 'info':
            code = msg.pop('code', 0)
            if not code:
                logger.info('Connection acknowledged')
            elif code == Code.EVT_STOP:
                # @Todo handle reconnect
                logger.info('Server stopped. Reconnect later')
            elif code == Code.EVT_RESYNC_START:
                # @Todo handle reconnect
                logger.info('Server resyncing. Reconnect later')
            elif code == Code.EVT_RESYNC_STOP:
                # @Todo handle reconnect
                logger.info('Server stopped. Reconnecting')

        elif bfx_event == 'error':
            code = msg['code']
            event_msg = msg['msg']

            if code not in Code or code == Code.ERR_UNK:
                logger.error('{}:Unknown error', code)
            elif code == Code.ERR_READY:
                # @Todo not ready to reconnect
                pass
            else:
                logger.error('{}:{}', code, event_msg)

        elif bfx_event == 'subscribed':
            cid, event = encode_event(msg)
            self._id_event[cid] = event
            logger.info('Subscription success "{}":{}', event, cid)

        elif bfx_event == 'pong':
            pass

        else:
            raise BadMessage(msg)

    def _handleUpdate(self, msg):
        # Ignore heartbeat
        if msg[1] == 'hb':
            logger.info('Heartbeat {}', msg[0])
            return
        cid = msg.pop(0)
        event = self._id_event[cid]
        for cb in self._callbacks[event]:
            # e.g. msg == ['tu', [<trade id>, <unixtime>, <volume>, <price>]]
            if isinstance(msg[0], str):
                cb(msg[1])
            else:
                cb(msg)
