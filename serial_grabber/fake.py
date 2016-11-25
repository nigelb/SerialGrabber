# Fake XBee

import argparse
import sys
import time
from xbee.zigbee import ZigBee
from serial_grabber.connections import TcpClient


def api_responses_as_commands():
    ret = {}
    for id_ in ZigBee.api_responses:
        response = ZigBee.api_responses[id_]
        ret[response['name']] = [{'name': 'id',
                                  'len': 1,
                                  'default': id_}] + response['structure']
    return ret


def api_commands_as_responses():
    ret = {}
    for cmd in ZigBee.api_commands:
        command = ZigBee.api_commands[cmd]
        ret[command[0]['default']] = {'name': cmd, 'structure': command[1:]}
    return ret


class ZigBeeDevice(ZigBee):
    api_commands = api_responses_as_commands()
    api_responses = api_commands_as_responses()


class FakeXbee(object):
    """
    Fake XBee using a TCP connection.
    """

    def __init__(self, address, port):
        self._address = address
        self._port = port

    def _setup(self):
        self._con = TcpClient(self._address, self._port)
        self._con.connect()
        self._radio = ZigBeeDevice(self._con, callback=self._handle_frame,
                                   error_callback=self._handle_error)
        print ZigBeeDevice.api_commands

    def _handle_frame(self, frame):
        if frame['command'] == 'AI':
            self._radio.send('at_response', frame_id=frame['frame_id'],
                                            command='AI',
                                             status=b'\x00')
        print frame

    def _handle_error(self, e):
        print "Error", str(e)

    def run(self):
        self._setup()
        try:
            while True:
                time.sleep(1)
                self._radio.send('rx', source_addr_long=b'01234567',
                                 source_addr=b'12', options=b'\x00',
                                 rf_data=b'HELLO')
        except KeyboardInterrupt:
            pass
        self._radio.halt()


def main():
    parser = argparse.ArgumentParser("Fake XBee module")
    parser.add_argument('sg_address', help="Serial grabber address")
    parser.add_argument('sg_port', type=int, help="Serial grabber port")

    args = parser.parse_args()

    FakeXbee(args.sg_address, args.sg_port).run()

if __name__ == '__main__':
    sys.exit(main())
