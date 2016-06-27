import zmq
from zmq.utils.monitor import recv_monitor_message
import msgpack as serializer

def filterEventsWithTopic(events,topic):
    """Returns all elements of ``events`` starting with ``topic``

    ``Topic`` refers to a general subscription term (e.g. ''notify.''). An ``event`` is the specific encountered message ``topic`` (e.g.
        ''notify.calibration.successful'')

    Args:
        events (string list): List of events
        topic (string): Topic to filter with

    Returns:
        string list: All elements of ``events`` starting with ``topic``
    """
    starts_with_filter = lambda e: e.startswith(topic)
    return filter(starts_with_filter, events)

def filterTopicsWithEvent(topics,event):
    """Returns all elements of ``topics`` with whom ``event`` starts with

    Args:
        topics (string list): List of topics
        event (string): Event to filter with

    Returns:
        string list: Returns all elements of ``topics`` with whom ``event``
            starts with
    """
    starts_with_filter = lambda t: event.startswith(t)
    return filter(starts_with_filter, topics)

class Requester(object):
    """
    Send commands or notifications to Pupil Remote
    """
    def __init__(self, ctx, url, block_unitl_connected=True):
        self.socket = zmq.Socket(ctx,zmq.REQ)
        if block_unitl_connected:
            #connect node and block until a connecetion has been made
            monitor = self.socket.get_monitor_socket()
            self.socket.connect(url)
            while True:
                status =  recv_monitor_message(monitor)
                if status['event'] == zmq.EVENT_CONNECTED:
                    break
                elif status['event'] == zmq.EVENT_CONNECT_DELAYED:
                    pass
                else:
                    raise Exception("ZMQ connection failed")
            self.socket.disable_monitor()
        else:
            self.socket.connect(url)

    def send_cmd(self,cmd):
        self.socket.send(cmd)
        return self.socket.recv()

    def notify(self,notification):
        topic = 'notify.' + notification['subject']
        payload = serializer.dumps(notification)
        self.socket.send_multipart((topic,payload))
        return self.socket.recv()

    def __del__(self):
        self.socket.close()