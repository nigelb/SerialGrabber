# Fake Serially connected buoy

import time
from serial_grabber.extractors import TransactionExtractor


class FakeSerial(object):
    """
    Fake serially connected buoy.

    This implementation is not threadsafe.
    """

    def __init__(self, con):
        self._con = con

    def _setup(self):
        self._con.connect()
        self._extractor = TransactionExtractor(0, 'BEGIN', 'END',
                                               self._handle_payload)

    def _handle_payload(self, stream_id, payload):
        print payload

    def run(self):
        self._setup()
        try:
            while True:
                self._extractor.write(self._con.read())
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        self._con.close()
