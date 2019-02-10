"""Class for processing broadcasts in Timeseries.

This module provides fine grain control as to the processing of broadcasts of the
Timeseries objects.

In addition to the naive approach of updating Timeseries cache whenever a non-zero value
is returned from a GenericTS / Timeseries evaluate function, current tools include the
use of the MemoryTS.execute decorator in GenericTS. By passing a Timestamp object to the
last argument of the eval_func of a GenericTS, we could make control updating of
Timeseries.

A Timeseries can opt for using UpdateStatus as one of the methods of controlling the
constraints of broadcasting and updating. The information of each TS subscriber would be
obtained from the construction of this class. If no additional information was provided
for updating, the naive approach would be used. The Timeseries concerned would hold
the update cascade until receiving all the broadcast signals from its subscriber.

Several modes of specifying update constraint has been encountered during usage. One
would be requiring all the timeseries to update within the same update episode in order
to allow broadcast.  Another would be specifying the exact time for the subscriber to
update, in case the Timeseries was timestamped. Yet another possible mode of control
would be specifying the number of broadcasts received for each subscriber before proceed
to updating.

This module intends to be an abstraction that allows effective implementation of all
these modes of updating and allows easy extension of any mode of processing broadcasts in
Timeseries in the future.

"""

from typing import List

import logging

logger = logging.getLogger(__name__)


class UpdateStatus:
    def __init__(self, update_mode: str, publishers):
        self.update_mode = update_mode
        self.publishers = publishers
        self.publishers_broadcasted = set()

    def handleBroadcast(self, ts, pos):
        status = None
        if self.update_mode == 'näive':
            status = self.näiveHandle(pos)
        elif self.update_mode == 'concurrent':
            status = self.concurrentHandle(ts, pos)
        else:
            raise NotImplementedError('UpdateStatus in progress...')
        return status

    def concurrentHandle(self, ts, pos):
        graph = ts.__class__.graph
        # from graph retrieve all the source
        if graph.inDegree(ts) == 1:
            logger.debug(
                'Obj: {}. All publisher broadcasted, proceed to updating', type(self)
            )
            return 'clear'
        else:
            for predecessor in graph.predecessors(ts):
                # print(repr(predecessor), graph.attr(predecessor, 'is_broadcasted'))
                if graph.attr(predecessor, 'is_broadcasted'):
                    pass
                else:
                    return 'hold'
            return 'clear'

    # Todo change type(self) to appropriate object
    def näiveHandle(self, pos):
        """Handle the broadcast as in original implementation"""
        if len(self.publishers) == 1:
            logger.debug(
                'Obj: {}. All publisher broadcasted, proceed to updating', type(self)
            )
            return 'clear'
        else:
            self.publishers_broadcasted.add(self.publishers[pos])

            if len(self.publishers_broadcasted) < len(self.publishers):
                logger.debug(
                    'Obj: {}. Number of publisher broadcasted: {}',
                    type(self),
                    len(self.publishers_broadcasted),
                )
                logger.debug(
                    'Obj: {}. Number of publisher remaining: {}',
                    type(self),
                    len(self.publishers) - len(self.publishers_broadcasted),
                )
                return 'hold'
            else:
                self.publishers_broadcasted.clear()
                logger.debug(
                    'Obj: {}. All publisher broadcasted, proceed to updating',
                    type(self),
                )
                return 'clear'
