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

This module intends to be an abstraction that allows the effective implementation of all
these modes of updating and allows easy extension of any mode of processing brodacsts in
Timeseries in the future.

"""

class UpdateStatus:
    pass
