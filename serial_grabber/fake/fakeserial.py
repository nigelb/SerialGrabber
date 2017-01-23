# Fake Serially connected buoy

import time
from serial_grabber.extractors import TransactionExtractor
import logging
import random


logger = logging.getLogger(__name__)


def parse_payload(stream_id, payload):
    lines = payload.split('\n')
    msg = lines[1]
    cmd = lines[2]
    parts = msg.split(' ')
    return (parts[0], parts[1], cmd)


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
        self._extractor = TransactionExtractor(0, 'BEGIN', 'END')

        self._state = None

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
                self._transition(self._state.run())
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        self._con.close()

    def read_payload(self):
        """
        Reads the connection for a complete payload
        """
        while True:
            d = ' '
            while len(d) > 0:
                d = self._con.read()
                if len(d) > 0:
                    logger.debug("Recieved Data: %s" % d)
                    output = self._extractor.write(d)
                    if output is not None:
                        return parse_payload(output[0], output[1])

            time.sleep(0.5)

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

    def process_message(self, cmd, tx_id, *args, **kwargs):
        """
        Process a message received from the serial grabber and optionally
        return a state transition.

        :returns:State or None:perform a state transition
        """
        raise NotImplementedError()

    def run(self):
        """
        The method that will be run periodically and is where the state's
        main loop logic is.

        :returns:State or None:perform a state transition
        """
        raise NotImplementedError()

    def send_mode_response(self, mode):
        """
        Sends a mode response, using the tx_id if it was set on the state data
        """
        tx_id = ''
        if 'tx_id' in self._data:
            tx_id = self._data['tx_id']

        self._node.send('RESPONSE ' + tx_id, "MODE: mode: " + mode)

    def send_cmd_response(self, cmd, params={}, tx_id=None):
        """
        Acknowledge the request message
        """
        if tx_id is None and 'tx_id' in self._data:
            tx_id = self._data['tx_id']

        params = ','.join(['%s:%s' % (k, params[k]) for k in params])

        self._node.send('RESPONSE ' + tx_id, "%s: %s" % (cmd.upper(), params))

    def process_next_message(self):
        self._node.send('RETRIEVE', 'MESSAGE: identifier:%s' %
                        self._node._identifier)
        return self.process_message(*self._node.read_payload())


class AsleepState(State):
    """
    In the asleep state the node does nothing except wait to wake up.
    """
    def init(self):
        self._next = time.time() + 10

    def process_message(self, cmd, tx_id, *args, **kwargs):
        logger.warn("Received a message while asleep %s" % cmd)

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
        if 'tx_id' not in self._data:
            logger.info('Sending HELLO with identifier %s' %
                        self._node._identifier)
            self._node.send('NOTIFY',
                            'HELLO: identifier: %s, version: 0.99' %
                            self._node._identifier)
        else:
            self.send_mode_response('live')

    def process_message(self, cmd, tx_id, args):
        logger.info('got %s %s %s' % (cmd, str(tx_id), args))
        if cmd == 'MODE':
            target = args
            if target == 'maintenance':
                return MaintenanceState, {'tx_id': tx_id}

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
            transition = self.process_next_message()
            if transition is not None:
                return transition


class MaintenanceState(State):
    def init(self):
        self._timeout = time.time() + 60
        self.send_mode_response('maintenance')

    def process_message(self, cmd, tx_id, args):
        logger.info('got %s %s %s' % (cmd, str(tx_id), args))
        if cmd == 'MODE':
            target = args
            if target == 'live':
                return LiveState, {'tx_id': tx_id}
            elif target == 'calibrate':
                return CalibrateState, {'tx_id': tx_id}

    def run(self):
        transition = self.process_next_message()
        if transition is not None:
            return transition

        if self._timeout > time.time():
            return
        return LiveState


class CalibrateState(State):
    def init(self):
        self._timeout = time.time() + 60
        self.send_mode_response('calibrate')

    def process_message(self, cmd, tx_id, args):
        logger.info('got %s %s %s' % (cmd, str(tx_id), args))
        self._timeout = time.time() + 60

        if cmd == 'MODE':
            target = args
            if target == 'live':
                return LiveState, {'tx_id': tx_id}
            elif target == 'maintenance':
                return MaintenanceState, {'tx_id': tx_id}
        elif cmd == 'CALIBRATE':
            args = args.split(',')
            data = dict([p.split(':') for p in args])
            if data['sensor'] == 'ph':
                return CalibratePh, {'tx_id': tx_id, 'params': data}
            if data['sensor'] == 'ec':
                return CalibrateEC, {'tx_id': tx_id, 'params': data}

    def run(self):
        transition = self.process_next_message()
        if transition is not None:
            return transition

        if self._timeout > time.time():
            return
        return LiveState


class CalibratePh(State):
    """
    pH calibration state, which will handle 1, 2 and 3 point calibrations.
    """
    def init(self):
        self._calibrate_tx_id = None
        self._timeout = time.time() + 60
        self.send_cmd_response('calibrate')

    def process_message(self, cmd, tx_id, args):
        logger.info('got %s %s %s' % (cmd, str(tx_id), args))
        self._timeout = time.time() + 60
        if cmd == 'CALIBRATE':
            args = args.split(',')
            data = dict([p.split(':') for p in args])
            if 'command' in data and data['command'] == 'accept':
                self.send_cmd_response('calibrate', {'sensor': self._sensor,
                                                     'phase': self._phase,
                                                     'slot': self._slot,
                                                     'command': 'accept'},
                                       tx_id=tx_id)
                if (int(data['phase']) + 1) == int(data['points']):
                    # Completed so return to calibrate state
                    return CalibrateState
                else:
                    self._calibrate_tx_id = None
            else:
                # This will start the calibrations
                self._calibrate_tx_id = tx_id
                self._sensor = 'ph'
                self._phase = int(data['phase'])
                self._slot = data['slot']
                self._value = float(data['fluid_value'])

    def run(self):
        if self._timeout < time.time():
            return LiveState

        if self._calibrate_tx_id is not None:
            self._send_reading()

        transition = self.process_next_message()
        if transition is not None:
            return transition

    def _send_reading(self):
        v = self._value * (random.randrange(90, 110) / 100.0)
        self.send_cmd_response('calibrate', {'sensor': self._sensor,
                                             'phase': self._phase,
                                             'slot': self._slot,
                                             'value': v},
                               tx_id=self._calibrate_tx_id)

class CalibrateEC(State):
    """
    EC calibration state, which will handle 1 and 2 point calibrations.
    """
    def init(self):
        self._calibrate_tx_id = None
        self._timeout = time.time() + 60
        self.send_cmd_response('calibrate')

    def process_message(self, cmd, tx_id, args):
        logger.info('got %s %s %s' % (cmd, str(tx_id), args))
        self._timeout = time.time() + 60
        if cmd == 'CALIBRATE':
            args = args.split(',')
            data = dict([p.split(':') for p in args])
            if 'command' in data and data['command'] == 'accept':
                self.send_cmd_response('calibrate', {'sensor': self._sensor,
                                                     'phase': self._phase,
                                                     'slot': self._slot,
                                                     'command': 'accept'},
                                       tx_id=tx_id)
                if (int(data['phase']) + 1) == int(data['points']):
                    # Completed so return to calibrate state
                    return CalibrateState
                else:
                    self._calibrate_tx_id = None
            else:
                # This will start the calibrations
                self._calibrate_tx_id = tx_id
                self._sensor = 'ec'
                self._phase = int(data['phase'])
                self._slot = data['slot']
                self._value = float(data['fluid_value'])

    def run(self):
        if self._timeout < time.time():
            return LiveState

        if self._calibrate_tx_id is not None:
            self._send_reading()

        transition = self.process_next_message()
        if transition is not None:
            return transition

    def _send_reading(self):
        v = self._value * (random.randrange(90, 110) / 100.0)
        self.send_cmd_response('calibrate', {'sensor': self._sensor,
                                             'phase': self._phase,
                                             'slot': self._slot,
                                             'value': v},
                               tx_id=self._calibrate_tx_id)