# IBAPI

A couple of things/definitions/conventions:

* a __low level message__ is some data prefixed with its size
* a __high level message__ is a list of fields separated by the NULL character;
  the fields are all strings; the message ID is the first field, the come others
  whose number and semantics depend on the message itself
* a __request__ is a message from client to TWS/IBGW (IB Gateway)
* an __answer__ is a message from TWS/IBGW to client


How the code is organized:

* __comm__ module: has tools that know how to handle (eg: encode/decode) low and
  high level messages
* __Connection__: glorified socket
* __Reader__: thread that uses Connection to read packets, transform to low
  level messages and put in a Queue
* __Decoder__: knows how to take a low level message and decode into high level
  message
* __Client__:
  + knows to send requests
  + has the message loop which takes low level messages from Queue and uses
    Decoder to tranform into high level message with which it then calls the
    corresponding Wrapper method
* __Wrapper__: class that needs to be subclassed by the user so that it can get
  the incoming messages


The info/data flow is:

* receiving:
  + __Connection.recv_msg()__ (which is essentially a socket) receives the
    packets
    - uses __Connection._recv_all_msgs()__ which tries to combine smaller
      packets into bigger ones based on some trivial heuristic
  + __Reader.run()__ uses __Connection.recv_msg()__ to get a packet and then
    uses __comm.read_msg()__ to try to make it a low level message. If that
    can't be done yet (size prefix says so) then it waits for more packets
  + if a full low level message is received then it is placed in the Queue
    (remember this is a standalone thread)
  + the main thread runs the __Client.run()__ loop which:
    - gets a low level message from Queue
    - uses __comm.py__ to translate into high level message (fields)
    - uses __Decoder.interpret()__ to act based on that message
  + __Decoder.interpret()__ will translate the fields into function parameters
    of the correct type and call with the correct/corresponding method of
    __Wrapper__ class

* sending:
  + __Client__ class has methods that implement the _requests_. The user will
    call those request methods with the needed parameters and __Client__ will
    send them to the TWS/IBGW.


Implementation notes:

* the __Decoder__ has two ways of handling a message (esentially decoding the
  fields)
    + some message very neatly map to a function call; meaning that the number
      of fields and order are the same as the method parameters. For example:
      Wrapper.tickSize(). In this case a simple mapping is made between the
      incoming msg id and the Wrapper method:

    IN.TICK_SIZE: HandleInfo(wrap=Wrapper.tickSize),

    + other messages are more complex, depend on version number heavily or need
      field massaging. In this case the incoming message id is mapped to a
      processing function that will do all that and call the Wrapper method at
      the end. For example:

    IN.TICK_PRICE: HandleInfo(proc=processTickPriceMsg),
