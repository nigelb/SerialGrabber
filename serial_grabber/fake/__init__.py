# Fake XBee

import argparse
import sys
from serial_grabber.connections import TcpClient
from serial_grabber.fake.fakexbee import FakeXbee
from serial_grabber.fake.serial import FakeSerial


def main():
    parser = argparse.ArgumentParser("Fake XBee module")
    parser.add_argument('sg_address', help="Serial grabber address")
    parser.add_argument('sg_port', type=int, help="Serial grabber port")
    parser.add_argument('type', help="Type of fake",
                        choices=['xbee', 'serial'])

    args = parser.parse_args()

    con = TcpClient(args.sg_address, args.sg_port)

    if args.type == 'xbee':
        FakeXbee(con).run()
    elif args.type == 'serial':
        FakeSerial(con).run()

if __name__ == '__main__':
    sys.exit(main())
