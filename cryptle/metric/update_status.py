"""Class for processing broadcasts in Timeseries.

This module implements UpdateStatus, which interprets the graph status in order to
determine the broadcasts of the Timeseries objects, and interfaces with the Timeseries
base class.

A Timeseries can opt for using UpdateStatus as one of the methods of controlling the
constraints of broadcasting and updating. The information of each TS subscriber would be
obtained from the construction of this class. If no additional information was provided
for updating, the naive approach would be used. The Timeseries concerned would suspend
the updating cascade until receiving all the broadcast signals from its subscriber.

Several modes of specifying update constraint has been encountered during usage. One
would be requiring all the timeseries to update within the same update episode in order
to allow broadcast.  Another would be specifying the exact time for the subscriber to
update, in case the Timeseries was timestamped. Yet another possible mode of control
would be specifying the number of broadcasts received for each subscriber before proceed
to updating.


"""

from typing import List
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


class UpdateStatus:
    """Class for handling TSGraph information and interfacing with Timeseries base
    class.

    This module intends to be an abstraction that allows effective implementation
    of all these modes of updating and allows easy extension of any mode of
    processing broadcasts in Timeseries in the future.

    Args
    ----
    ts: Timeseries
        The actual concrete Timeseries object using the service of the graph.
    update_mode : str
        Choice of updating mode, can be 'naive', 'concurrnet', 'daily'.
    publishers: list
        List of publishers that this Timeseries listens to.

    """

    def __init__(self, ts, update_mode: str, publishers):
        self.ts = ts
        self.update_mode = update_mode
        # Consider reviewing - transition to the graph construct instead of using set
        self.publishers = publishers
        self.publishers_broadcasted = set()

    def handleBroadcast(self, ts, pos) -> str:
        """Public interface for Timeseries base class to call.

        A ``status`` string of either 'hold' or 'clear' would be returned back to the
        Timeseires base class caller. 'clear' would mean that the Timeseries is clear
        for updating while 'hold' suspends the updating cascade.

        Args
        ----
        ts: Timeseries
            The actual timeseries object that needs to process that broadcast.
        pos: int
            The index of publisher that broadcasted the update

        """

        status = None
        if self.update_mode == 'naive':
            status = self.naiveHandling(pos)
        elif self.update_mode == 'concurrent':
            status = self.concurrentHandling(ts)
        elif self.update_mode == 'conditional':
            status = self.conditionalHandling(ts, pos)
        elif self.update_mode == 'daily':
            status = self.dailyTimeHandling(ts, pos)
        elif self.update_mode == 'exact':
            status = self.exectTimeHandling(ts, pos)
        else:
            raise NotImplementedError('UpdateStatus in progress...')

        if status is None:
            raise ValueError('Update status is not correctly handled.')

        return status

    def dailyTimeHandling(self, ts, pos):
        """Check whether the current timestmap matches to the daily execute time.
        Proceed to naiveHanlding if passed."""
        graph = ts.__class__.graph

        if datetime.fromtimestamp(ts.timestamp).time() in graph.getExecuteTime(
            ts.timestamp, ts
        ):
            pass
        else:
            return 'hold'

        return self.naiveHandling(pos)

    def exactTimeHandling(self, ts, pos):
        """To be implemented"""
        raise NotImplementedError()

    def conditionalHandling(self, ts, pos):
        """To be implemented"""
        raise NotImplementedError()

    def concurrentHandling(self, ts):
        """Handles the broadcast according to indiviudal broadcasting episode."""
        graph = ts.__class__.graph

        if graph.inDegree(ts) == 1:
            logger.debug(
                'Obj: {}. All publisher broadcasted, proceed to updating', type(self)
            )
            return 'clear'
        else:
            for predecessor in graph.predecessors(ts):
                if graph.attr(predecessor, 'is_broadcasted'):
                    pass
                else:
                    return 'hold'
            return 'clear'

    # Todo change type(self) to appropriate object
    def naiveHandling(self, pos):
        """Handle the broadcast as in original implementation."""
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
