# Fake Serially connected buoy

import time
from serial_grabber.extractors import TransactionExtractor


MODE_RUN = 'run'
MODE_MAINTENANCE = 'maintenance'


class FakeSerial(object):
    """
    Fake serially connected buoy.

    This implementation is not threadsafe.
    """

    def __init__(self, con):
        self._con = con
        self._identifier = 'default_buoy'

    def _setup(self):
        self._con.connect()
        self._extractor = TransactionExtractor(0, 'BEGIN', 'END',
                                               self._handle_payload)
        self._mode = MODE_RUN
        self._timeout = None
        self._last_data = None

    def _handle_payload(self, stream_id, payload):
        lines = payload.split('\n')
        line = lines[1]
        parts = line.split(' ')
        print parts
        if parts[0] == 'MODE':
            self._cmd_mode(parts[1])

    def _cmd_mode(self, mode):
        """
        Change the mode of the buoy.
        """
        if mode == MODE_MAINTENANCE:
            self._mode = MODE_MAINTENANCE
            self._timeout = time.time() + 60
        elif mode == MODE_RUN:
            self._mode = MODE_RUN
            self._timeout = None
        else:
            self._send_error('INVALID MODE')
            return
        # Acknowledge the mode switch
        self._send('RESPONSE', "MODE: mode: %s" % mode)

    def _process(self):
        """
        Perform work based on the current mode of the system
        """
        if self._mode == MODE_RUN:
            if self._last_data is None or time.time() - self._last_data > 10:
                self._send_data()
        elif self._mode == MODE_MAINTENANCE:
            if time.time() > self._timeout:
                self._cmd_mode(MODE_RUN)
                return

    def _send(self, message_type, data):
        """
        Sends the payload wrapped in the appropriate headers
        """
        payload = """BEGIN
%s
%s
END
"""
        self._con.write(payload % (message_type, data))

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
        self._send('NOTIFY',
                   'HELLO: identifier: %s, version: 0.99' % self._identifier)

    def run(self):
        self._setup()
        # Hack to get around startup threshold
        time.sleep(5)
        self._send_hello()
        try:
            while True:
                self._extractor.write(self._con.read())

                self._process()
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        self._con.close()
