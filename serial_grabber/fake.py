# Fake XBee

import argparse
import sys
from xbee.zigbee import ZigBee
from serial_grabber.connections import TcpClient


def api_responses_as_commands():
    ret = {}
    for id_ in ZigBee.api_responses:
        response = ZigBee.api_responses[id_]
        ret[response['name']] = [{'name': 'id',
                                  'len': 1,
                                  'default': id_},
                                 {'name': 'frame_id',
                                  'len': 1,
                                  'default': b'\x01'}] + response['structure']
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
        print self._radio.api_responses

    def _handle_frame(self, frame):
        if frame['command'] == 'AI':
            self._radio.send('at_response', frame_id=frame['frame_id'],
                                            command='AI',
                                             status=b'\x00')
        print frame

    def _handle_error(self, e):
        print str(e)

    def run(self):
        self._setup()
        self._radio.join()


def main():
    parser = argparse.ArgumentParser("Fake XBee module")
    parser.add_argument('sg_address', help="Serial grabber address")
    parser.add_argument('sg_port', type=int, help="Serial grabber port")

    args = parser.parse_args()
    import manhole; manhole.install()
    FakeXbee(args.sg_address, args.sg_port).run()

if __name__ == '__main__':
    sys.exit(main())
