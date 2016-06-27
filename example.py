# Add module to your Python path.
# This is just a temporal solution until this package is distributed via pip
import sys
sys.path.append("./pupil_interface")

import time
from pupil_interface import Communicator
from pupil_interface import utils

# define a simple callback
def handle_notification(topic, data):
    print topic, data

# Instanciate `Communicator`. Will raise exception on connection errors.
try:
    interface = Communicator()
except Exception as e:
    print '%s, the remote host might be unavailable'%e
    exit()

# Send a notification.
print 'Simulating calibration...'
interface.notify({'subject':'calibration.successful'})

# Wait for one of two events
cal_suc = 'notify.calibration.successful'
cal_stopped = 'notify.calibration.stopped'
encountered = interface.waitAnyEvent([cal_suc,cal_stopped])

# Check if `cal_suc` was encountered
if cal_suc in encountered:

    # Add callback for pupil data
    print 'Calibration successful. Subscribing to pupil data...'
    interface.addCallbackForEvents(handle_notification, ['pupil'])

    # Handle pupil data for `sub_time`. Stop after `break_time`.
    sub_time = 1.
    break_time = 3.
    start = time.time()
    subscribed = True

    while True:
        # Check for new events. Will call callbacks accordingly.
        interface.checkEvents()
        # Sleep to prevent busy loop.
        time.sleep(.05)

        # Check if pupil data subscription is still necessary
        if time.time() - start > sub_time and subscribed:
            # Remove pupil data callback
            interface.removeCallbackForEvents(handle_notification, ['pupil'])
            subscribed = False
            print 'Unsubscribed from pupil data'

        # Exir after `break_time` is over
        if time.time() - start > break_time:
            break
print 'exit...'
