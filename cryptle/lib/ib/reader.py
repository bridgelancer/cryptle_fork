"""
Copyright (C) 2018 Interactive Brokers LLC. All rights reserved. This code is subject to the terms
and conditions of the IB API Non-Commercial License or the IB API Commercial License, as applicable.
"""


"""
The EReader runs in a separate threads and is responsible for receiving incoming
messages. It will read the packets from the wire, use the low level IB messaging to
remove the size prefix and put the rest in a Queue.
"""

import errno
import threading

from . import comm
from .common import get_ib_logger


logger = get_ib_logger(__name__.split('.')[-1])


class EReader(threading.Thread):
    """Producer of incoming TWS message queue."""

    def __init__(self, conn, msg_queue):
        super().__init__()
        self.conn = conn
        self.msg_queue = msg_queue

    def run(self):
        buf = b""
        while self.conn.isConnected():
            try:
                data = self.conn.recvMsg()
            except OSError as e:
                if e.errno == errno.EBADF and not self.conn.isConnected():
                    break
                else:
                    logger.error(e)

            logger.debug("reader loop, recvd size %d", len(data))
            buf += data

            while len(buf) > 0:
                (size, msg, buf) = comm.read_msg(buf)
                if msg:
                    logger.debug("putting %d bytes message to reader queue", len(msg))
                    self.msg_queue.put(msg)
                else:
                    logger.debug("more incoming packet(s) are needed ")
                    break

        logger.debug("EReader thread finished")
