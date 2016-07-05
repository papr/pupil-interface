# Pupil Interface

A Python module which uses `Pupil Remote` and the `IPC Backbone` feature introduced in [v0.8](https://github.com/pupil-labs/pupil/releases/tag/v0.8) to communicate remotely to Pupil applocations like `Pupil Capture` and `Pupil Service`.

## Examples
See [`example.py`](example.py) for an full example.

Initialization

```python
from pupil_interface import Communicator
try:
    interface = Communicator(address='tcp://127.0.0.1', req_port=50020)
except Exception as e:
    print '%s, the remote host might be unavailable'%e
```

Recording:

```python
interface.startRecording(session_name="Pupil Interface Recording")
# do other stuff...
interface.stopRecording()
```

Wait for specific events:

```python
interface.startCalibration()
cal_suc = 'notify.calibration.successful'
cal_stopped = 'notify.calibration.stopped'
encountered = interface.waitAnyEvent([cal_suc,cal_stopped])
if cal_suc in encountered:
    # Calibration was successful
    pass
else:
    # Calibration was not successful
    pass
```

Using callbacks:

```python
# define a simple callback
def handle_notification(topic, data):
    print topic, data

# Add callback and subscribe to `notify`
interface.addCallbackForEvents(handle_notification, ['notify'])
while True:
    # Do other stuff...
    interface.checkEvents() # Executes callback if necessary
```

## API Reference

###### `Communicator()`
Simple class to interface with Pupil applications. Connects to `Pupil Remote`, asks for `SUB_PORT` and creates two `zmq_tools.Msg_Receiver` to subscribe to notifications and other data.

Args:

- `ctx (zmq.Context,optional)`: zmq context
- `address (str, optional)`: Remote address
- `req_port (int, optional)`: Remote request port
- `block_unitl_connected (boolean, optional)`: Block until connected


###### `Communicator.startRecording()`
Starts recording session.

Args:

- `session_name (str, optional)`: Name for the recording session


###### `Communicator.stopRecording()`
Stops recording session.


###### `Communicator.startCalibration()`
Starts calibration procedure.


###### `Communicator.stopCalibration()`
Stops calibration procedure.


###### `Communicator.notify()`
Send a notification to the remote Pupil application.

Args:

- `notification (dict)`: Notification dictionary containing at least the `subject` key.


###### `Communicator.subscribe()`
Subscribes to `topic`.
Args:

- `topic (str)`: Subscription topic


###### `Communicator.unsubscribe()`
Unubscribes from `topic`.
Args:

- `topic (str)`


###### `Communicator.addCallbackForEvents()`
Registers a callback for a given list of events and automatically subscribes to the events in `events`.

Args:

- `callback (function)`: function which takes two arguments, event and data
- `events (string list)`: list of events


###### `Communicator.removeCallbackForEvents()`
Unregisters a callback for a given list of events and automatically unsubscribes from the events in `events`.

Args:

- `callback (function)`: function which takes two arguments, event and data
- `events (string list)`: list of events


###### `Communicator.callCallbacksForEvents()`
Executes all registered callbacks matching `events`.

Args:

- `events (dict)`: Dictionary with topic-data entries, e.g. returned by `pollEventsOnce()`.


###### `Communicator.pollEventsOnce()`
Used by ``checkEvents()``, `` waitAnyEvent()``, and ``waitAllEvents()`` for polling events.

Args:

- `timeout (None, optional)`: Poll timeout

Returns:

- `dictionary`: Contains topic-payload entries


###### `Communicator.checkEvents()`
Checks for all available events. Returns after execution of respective callbacks.

Returns:

- `dictionary`: Returns events in a dictionary, where the key is the
        event and the value its most recent payload


###### `Communicator.waitForEvents()`
Blocks until one or all events in ``looking_for`` were encountered. Returns after execution of respective callbacks.

Args:

- `wait_for_all (boolean)`: Specifies if all `events` need to occure before exiting.
- `looking_for (string array)`: List of event names
- `timeout (float, optional)`: Timeout in milliseconds.

Returns:

- `dictionary`: Contains topic-data entries


###### `Communicator.waitAnyEvent()`
Calls `waitForEvents()` with `wait_for_all = False`.


###### `Communicator.waitAllEvents()`
Calls `waitForEvents()` with `wait_for_all = True`.
