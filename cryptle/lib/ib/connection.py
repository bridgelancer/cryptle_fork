"""
Copyright (C) 2018 Interactive Brokers LLC. All rights reserved. This code is subject to the terms
and conditions of the IB API Non-Commercial License or the IB API Commercial License, as applicable.
"""


"""
Just a thin wrapper around a socket.
It allows us to keep some other info along with it.
"""


import socket
import threading

from .common import *
from .errors import *


# TODO: support SSL !!
logger = get_logger(__name__.split('.')[-1])


class Connection:
    """Encapsulation for basic socket I/O with logging.

    This class does not capture exceptions. Exception handling are delegated to higher
    level classes responsible for connection logics.
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.wrapper = None
        self.lock = threading.Lock()

    def connect(self):
        try:
            self.socket = socket.socket()
        except socket.error:
            if self.wrapper:
                self.wrapper.error(
                    NO_VALID_ID, FAIL_CREATE_SOCK.code(), FAIL_CREATE_SOCK.msg()
                )

        self.socket.connect((self.host, self.port))
        self.socket.settimeout(1)  # non-blocking

    def disconnect(self):
        with self.lock:
            self.socket.close()
            self.socket = None
            logger.info("socket closed")
            if self.wrapper:
                self.wrapper.connectionClosed()

    def isConnected(self):
        # TODO: also handle when socket gets interrupted/error
        return self.socket is not None

    def sendMsg(self, msg):
        with self.lock:
            if not self.isConnected():
                logger.debug("sendMsg attempted while not connected")
                return 0
            try:
                logger.debug("sendMsg bytes:%d, raw:%s|", len(msg), msg)
                nSent = self.socket.send(msg)
            except socket.timeout:
                pass

        logger.debug("sentMsg: %d bytes", nSent)

        return nSent

    def recvMsg(self):
        buf = b""
        if not self.isConnected():
            logger.debug("recvMsg attempted while not connected")
            return buf

        try:
            buf = self._recvAllMsg()
        except socket.timeout:
            pass
        return buf

    def _recvAllMsg(self):
        cont = True
        allbuf = b""

        while cont:
            buf = self.socket.recv(4096)
            allbuf += buf
            logger.debug("recvMsg bytes:%d, raw:%s|", len(buf), buf)

            if len(buf) < 4096:
                cont = False

        return allbuf
