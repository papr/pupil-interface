import zmq, time
from zmq_tools import Msg_Receiver, Msg_Dispatcher
from utils import Requester, filterTopicsWithEvent, filterEventsWithTopic

class Communicator(object):
    '''Interface for communication with Pupil applications

    Uses classes provided by the ``zmq_tools`` to integrate different types
        of communication into one interface.

    Not threadsave. Make a new one for each thread.
    '''
    def __init__(self,ctx=zmq.Context(), address='tcp://127.0.0.1', req_port=50020, block_unitl_connected=True):
        """Simple class to interface with Pupil applications.

        Args:
            ctx (zmq.Context,optional): Description
            address (str, optional): Remote address
            req_port (int, optional): Remote request port
            block_unitl_connected (boolean, optional): Block until connected
        """
        # init requester
        self._req_url = '%s:%s'%(address,req_port)
        self.requester = Requester(ctx,self._req_url,block_unitl_connected=True)

        # the requester talks to Pupil remote and receives the session unique IPC SUB URL
        self._sub_port = self.requester.send_cmd('SUB_PORT')

        # init receiver for notifications
        self.mailman = Msg_Receiver(ctx, '%s:%s'%(address,self._sub_port), topics=())

        # init receiver for data, subscribe as necessary
        self.heavylifter = Msg_Receiver(ctx, '%s:%s'%(address,self._sub_port), topics=())

        self.poller = zmq.Poller()
        self.poller.register(self.mailman.socket,zmq.POLLIN)
        self.poller.register(self.heavylifter.socket,zmq.POLLIN)

        self.get_time = time.time
        self.callbacks = {}

    def startRecording(self,session_name=None):
        recording_cmd = 'R' if not session_name else 'R %s'%session_name
        self.requester.send_cmd(recording_cmd)
    def stopRecording(self):
        self.requester.send_cmd('r')

    def startCalibration(self):
        self.requester.send_cmd('C')
    def stopCalibration(self):
        self.requester.send_cmd('c')

    def notify(self,notification):
        '''Forwards to self.requester.notify()'''
        return self.requester.notify(notification)

    def pollEventsOnce(self,timeout=None):
        """Used by ``checkEvents`` and ``wait*`` for polling events.

        Polls and receives notification and events once for ``self.mailman``
            and once for ``self.heavylifter``

        Args:
            timeout (None, optional): Poll timeout

        Returns:
            dictionary: Contains topic-payload entries
        """
        events = {}

        # Poll for events
        items = dict(self.poller.poll(timeout=timeout))

        # Notifications
        if self.mailman.socket in items and items[self.mailman.socket] == zmq.POLLIN:
            topic, payload = self.mailman.recv()
            payload['_time_of_arrival_'] = time.time()
            events[topic] = payload

        # Events
        if self.heavylifter.socket in items and items[self.heavylifter.socket] == zmq.POLLIN:
            topic, payload = self.heavylifter.recv()
            payload['_time_of_arrival_'] = time.time()
            events[topic] = payload

        return events

    def checkEvents(self):
        """Checks for all available events

        Calls ``callCallbacksForEvents`` before returning.

        Returns:
            dictionary: Returns events in a dictionary, where the key is the
                event and the value its most recent payload
        """
        events = {}
        while True:
            found = self.pollEventsOnce(timeout=0.0)
            events.update(found)
            if not found:
                self.callCallbacksForEvents(events)
                return events

    def waitAnyEvent(self,looking_for,timeout=None):
        return self.waitForEvents(False,looking_for,timeout)

    def waitAllEvents(self,looking_for,timeout=None):
        return self.waitForEvents(True,looking_for,timeout)

    def waitForEvents(self,wait_for_all,looking_for,timeout=None):
        """Blocks until one or all events in ``looking_for`` were encountered

        Calls ``callCallbacksForEvents`` before returning.

        Args:
            wait_for_all (boolean): Specifies if
            looking_for (string array): List of event names
            timeout (float, optional): Timeout in milliseconds.

        Returns:
            dictionary: Contains topic-payload entries
        """
        if isinstance(looking_for, basestring):
            # We always look at a list of events.
            looking_for = [looking_for]
        else:
            # Make a mutable copy
            looking_for = looking_for[:]

        for topic in looking_for:
            temp_subscriptions = []
            if topic not in self.callbacks:
                self.subscribe(topic)
                temp_subscriptions.append(topic)

        found_at_least_one = False
        events = {}
        if timeout:
            t_checkpoint = self.get_time()

        while True:
            # Poll and merge into ``events``
            found = self.pollEventsOnce(timeout=timeout)
            events.update(found)
            # Test if we found what we were looking for
            for e in events:
                to_remove = filterTopicsWithEvent(looking_for,e)
                # once true always true
                found_at_least_one = found_at_least_one or len(to_remove) > 0
                looking_for = [t for t in looking_for if t not in to_remove]

            #      all found  or  wait for at least one + found at least one
            #   v-------------v      v--------------v     v----------------v
            if (not looking_for) or (not wait_for_all and found_at_least_one):
                break

            if timeout: # apply passed time to timeout
                timeout -= (self.get_time() - t_checkpoint)*1000
                t_checkpoint = self.get_time()
                # time is up
                if timeout <= 0:
                    break

        # unsubscribe from all temporal subscriptions
        for topic in temp_subscriptions:
            self.unsubscribe(topic)

        self.callCallbacksForEvents(events)
        return events

    def callCallbacksForEvents(self,events):
        for registered in self.callbacks:
            for matching_e in filterEventsWithTopic(events.keys(),registered):
                for cb_func in self.callbacks[registered]:
                    cb_func(matching_e, events[matching_e])

    def addCallbackForEvents(self, callback, events):
        '''Registers a callback for a list of events

        Adds a callback for a given list of events and automatically subscribes to the events in `events`.

        Args:
            callback (function): function which takes two arguments, event and data
            events (string list): list of events
        '''
        for event in events:
            try:
                self.callbacks[event].append(callback)
            except KeyError:
                self.callbacks[event] = [callback]
                self.subscribe(event)

    def removeCallbackForEvents(self, callback, events):
        '''Removes registered callback for specific events

        Args:
            callback (string array): list of events
        '''
        for event in events:
            try:
                self.callbacks[event] = filter(lambda cb: cb != callback, self.callbacks[event])
                if not self.callbacks[event]:
                    self.unsubscribe(event)
            except KeyError:
                print 'keyerror on',event
                pass

    def subscribe(self,topic):
        """Subscribe to ``self.mailman`` for notifications and to
            ``self.heavylifter`` for everything else
        """
        if topic.startswith('notify'):
            # print '[subscribe]', '<notify>', topic
            self.mailman.subscribe(topic)
        else:
            # print '[subscribe]', '<heavy>', topic
            self.heavylifter.subscribe(topic)

    def unsubscribe(self,topic):
        """Unsubscribe from ``self.mailman`` for notifications and from
            ``self.heavylifter`` for everything else
        """
        if topic.startswith('notify'):
            # print '[unsubscribe]', '<notify>', topic
            self.mailman.unsubscribe(topic)
        else:
            # print '[unsubscribe]', '<heavy>', topic
            self.heavylifter.unsubscribe(topic)

    def __del__(self):
        '''Replaces `close()`.'''
        if hasattr(self,'poller'):
            self.poller.unregister(self.mailman.socket)
            self.poller.unregister(self.heavylifter.socket)
            del self.poller
        if hasattr(self,'heavylifter'):
            del self.heavylifter
        if hasattr(self,'mailman'):
            del self.mailman
        if hasattr(self,'requester'):
            del self.requester

