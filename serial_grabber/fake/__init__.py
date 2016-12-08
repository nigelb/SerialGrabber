# Fake buoy entry point

import argparse
import sys
import logging

import serial

from serial_grabber.connections import TcpClient, SerialPort

try:
    from serial_grabber.fake.fakexbee import FakeXbee
    xbee_support = True
except:
    xbee_support = False
from serial_grabber.fake.fakeserial import FakeSerial


def setup_logging():
    FORMAT = '%(asctime)-15s %(levelname)-7s %(name)s %(filename)s:%(funcName)s:%(lineno)d - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)


def main():
    parser = argparse.ArgumentParser("Fake XBee module")
    subparser = parser.add_subparsers(description="Transport Methods", help="sub-command help.")
    parser.add_argument('protocol', help="Protocol to speak over the transport",
                         choices=['xbee', 'serial'])

    serial_p = subparser.add_parser('tty', help="Use a serial port for the transport.")
    serial_p.add_argument('port', help="Serial port to use")
    serial_p.add_argument('baud', type=int, help="Baud rate to use")
    serial_p.add_argument("--parity",metavar="<parity>", dest="parity", action="store", default=serial.PARITY_NONE, help="The parity for the XBee Module, default: PARITY_NONE. Values are PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE = 'N', 'E', 'O', 'M', 'S'")
    serial_p.add_argument("--stop-bits",metavar="<stop_bits>", dest="stop_bits", action="store", default=1, type=int, help="The stop bits for the XBee Module, default: 1")
    serial_p.add_argument("--timeout",metavar="<timeout>", dest="timeout", action="store", default=1, type=int, help="The timeout for the XBee Module, default: 1")
    serial_p.set_defaults(stream="serial")



    tcp_p = subparser.add_parser('tcp', help="Use a TCP stream for the transport.")
    tcp_p.add_argument('sg_address', help="Serial grabber address")
    tcp_p.add_argument('sg_port', type=int, help="Serial grabber port")
    tcp_p.set_defaults(stream="tcp")


    args = parser.parse_args()
    print args
    setup_logging()

    if args.stream == "tcp":
        con = TcpClient(args.sg_address, args.sg_port)
    elif args.stream == "serial":
        con = SerialPort(args.port, args.baud, args.timeout, args.parity, args.stop_bits)


    if args.protocol == 'xbee':
        if xbee_support:
            FakeXbee(con).run()
        else:
            print "XBee support not available"
    elif args.protocol == 'serial':
        FakeSerial(con).run()

if __name__ == '__main__':
    sys.exit(main())
