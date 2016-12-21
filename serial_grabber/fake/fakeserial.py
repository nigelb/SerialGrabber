# Fake Serially connected buoy

import time
from serial_grabber.extractors import TransactionExtractor
import logging


logger = logging.getLogger(__name__)


class FakeSerial(object):
    """
    Fake serially connected buoy.

    This implementation is not threadsafe.
    """

    def __init__(self, con, ack="OK", ack_timeout=5):
        self._con = con
        self._identifier = 'default_buoy'
        self._ack_timeout = ack_timeout
        self._ack = ack

    def _setup(self):
        self._con.connect()
        self._extractor = TransactionExtractor(0, 'BEGIN', 'END',
                                               self._handle_payload)
        self._state = None

    def _handle_payload(self, stream_id, payload):
        lines = payload.split('\n')
        line = lines[1]
        parts = line.split(' ')
        self._transition(self._state.request(parts[0], parts[1:]))

    def send(self, message_type, data, retry=5):
        """
        Sends the payload wrapped in the appropriate headers
        """
        payload = """%s
%s""" % (message_type, data)
        payload_wrapper = """BEGIN
%s
%s
END
"""
        wrapped = payload_wrapper % (payload, len(payload))
        count = 0
        while count < retry:
            self._con.write(wrapped)
            if self.read_ack():
                break
            count += 1
        return count < retry

    def _send_error(self, error):
        """
        Send an error payload
        """
        self.send('NOTIFY', 'ERROR: message: %s' % error)

    def run(self):
        self._setup()
        # Hack to get around startup threshold
        time.sleep(5)
        self._state = AsleepState(self)
        try:
            while True:
                d = ' '
                while len(d) > 0:
                    d = self._con.read()
                    if len(d) > 0:
                        logger.debug("Recieved Data: %s" % d)
                        self._extractor.write(d)

                self._transition(self._state.run())
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        self._con.close()

    def read_ack(self):
        start = time.time()
        data = ""
        while self._ack not in data and time.time() - start < self._ack_timeout:
            data += self._con.read(1)
        logger.debug("Ack found: %s" % (self._ack in data))
        return self._ack in data

    def _transition(self, transition):
        """
        Maybe transition
        """
        if transition is not None:
            logger.info("Transitioning to %s" % str(transition))
            if isinstance(transition, type):
                self._state = transition(self)
            else:
                self._state = transition[0](self, transition[1])


class State(object):
    """State machine state"""
    def __init__(self, node, data={}):
        self._node = node
        self._data = data
        self.init()

    def init(self):
        """
        Anything that needs to be done on entry to this state
        """

    def request(self, cmd, *args, **kwargs):
        """
        Send an event to the state machine.
        :returns:State or None:perform a state transition
        """
        raise NotImplementedError()

    def run(self):
        """
        The method that will be run periodically
        :returns:State or None:perform a state transition
        """
        raise NotImplementedError()


class AsleepState(State):
    def init(self):
        self._next = time.time() + 10

    def run(self):
        """
        Send a hello then transition to another state.
        """
        if self._next > time.time():
            return

        logger.info('Waking up')
        return LiveState


class LiveState(State):
    """
    In Live state we send data periodically
    """
    def init(self):
        self._next_data = time.time()
        self._next_sleep = time.time() + 60
        logger.info('Sending HELLO with identifier %s' % self._node._identifier)
        self._node.send('NOTIFY',
                        'HELLO: identifier: %s, version: 0.99' %
                        self._node._identifier)

    def request(self, cmd, nxt):
        logger.info('got %s %s' % (cmd, str(nxt)))

    def run(self):
        if self._next_sleep < time.time():
            return AsleepState
        elif self._next_data < time.time():
            data = """BATTERY: V_100:0, Solar_uA:14929,32
BOARD_TEMP: 28.36ef0a080000ca,3143,34
HEAD_TEMP: 28.a84102050000f5,2956,33
INERTIAL: AX:-1263,AY:8582,AZ:-569,GZ:146,GY:358,GZ:682,55
COMPASS: MX:-238,XY:224,MZ:-50,30
RGB: R:2619,G:2492,B:1127,W:4765,32
TRANSMISSION:32040, GAIN:8,26
SCATTER:2268, GAIN:8,20
GPS: FIX NOT_FOUND,18
PH: 7095,8
EC: 94729, TDS: 51154, PSS: 0,29
DO: 597, %S: 0,14"""
            self._node.send('DATA', data)
            self._next_data = time.time() + 10
        else:
            self._node.send('RETRIEVE', 'MESSAGE: identifier:%s' %
                            self._node._identifier)


class MaintenanceState(State):
    def init(self):
        self._timeout = time.time() + 60
        self._node.send('RESPONSE', "MODE: mode: maintenance")

    def run(self):
        if self._timeout > time.time():
            return
        return LiveState
