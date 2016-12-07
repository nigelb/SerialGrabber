# Fake buoy entry point

import argparse
import sys
import logging
from serial_grabber.connections import TcpClient
try:
    from serial_grabber.fake.fakexbee import FakeXbee
    xbee_support = True
except:
    xbee_support = False
from serial_grabber.fake.serial import FakeSerial


def setup_logging():
    FORMAT = '%(asctime)-15s %(levelname)-7s %(name)s %(filename)s:%(funcName)s:%(lineno)d - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)


def main():
    parser = argparse.ArgumentParser("Fake XBee module")
    parser.add_argument('sg_address', help="Serial grabber address")
    parser.add_argument('sg_port', type=int, help="Serial grabber port")
    parser.add_argument('type', help="Type of fake",
                        choices=['xbee', 'serial'])

    args = parser.parse_args()

    setup_logging()

    con = TcpClient(args.sg_address, args.sg_port)

    if args.type == 'xbee':
        if xbee_support:
            FakeXbee(con).run()
        else:
            print "XBee support not available"
    elif args.type == 'serial':
        FakeSerial(con).run()

if __name__ == '__main__':
    sys.exit(main())
