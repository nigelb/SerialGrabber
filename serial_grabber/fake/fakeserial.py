# Fake Serially connected buoy

import time
from serial_grabber.extractors import TransactionExtractor
import logging

MODE_LIVE = 'live'
MODE_MAINTENANCE = 'maintenance'


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
        self._mode = MODE_LIVE
        self._timeout = None
        self._last_data = None

    def _handle_payload(self, stream_id, payload):
        lines = payload.split('\n')
        line = lines[1]
        parts = line.split(' ')
        if parts[0] == 'MODE':
            self._cmd_mode(parts[1])

    def _cmd_mode(self, mode):
        """
        Change the mode of the buoy.
        """
        if mode == MODE_MAINTENANCE:
            self._mode = MODE_MAINTENANCE
            self._timeout = time.time() + 60
            logger.info('Mode -> maintenance timeout at %d' % (self._timeout, ))
        elif mode == MODE_LIVE:
            self._mode = MODE_LIVE
            self._timeout = None
            logger.info('Mode -> live')
        else:
            self._send_error('INVALID MODE')
            return
        # Acknowledge the mode switch
        self._send('RESPONSE', "MODE: mode: %s" % mode)

    def _process(self):
        """
        Perform work based on the current mode of the system
        """
        if self._mode == MODE_LIVE:
            if self._last_data is None or time.time() - self._last_data > 10:
                logger.info('Sending sample data')
                self._send_data()
        elif self._mode == MODE_MAINTENANCE:
            if time.time() > self._timeout:
                logger.info('Timed out of maintenance mode')
                self._cmd_mode(MODE_LIVE)
                return

    def _send(self, message_type, data, retry=5):
        """
        Sends the payload wrapped in the appropriate headers
        """
        payload = """%s
%s"""%(message_type, data)
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
            count+=1
        return count < retry

    def _send_data(self):
        """
        Send a data payload
        """
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
        self._send('DATA', data)
        self._last_data = time.time()

    def _send_error(self, error):
        """
        Send an error payload
        """
        self._send('NOTIFY', 'ERROR: message: %s' % error)

    def _send_hello(self):
        """
        Sends the hello message.
        """
        logger.info('Sending HELLO with identifier %s' % self._identifier)
        self._send('NOTIFY',
                   'HELLO: identifier: %s, version: 0.99' % self._identifier)

    def run(self):
        self._setup()
        # Hack to get around startup threshold
        time.sleep(5)
        self._send_hello()
        try:
            while True:

                d = ' '
                while len(d) > 0:
                    d = self._con.read()
                    if len(d) > 0:
                        logger.debug("Recieved Data: %s"%d)
                        self._extractor.write(d)
                self._process()
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        self._con.close()

    def read_ack(self):
        start = time.time()
        data = ""
        while self._ack not in data and time.time() - start < self._ack_timeout:
            data += self._con.read(1)
        logger.debug("Ack found: %s"%(self._ack in data))
        return self._ack in data
