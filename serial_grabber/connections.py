#!/usr/bin/env python
# SerialGrabber reads data from a serial port and processes it with the
# configured processor.
# Copyright (C) 2012  NigelB
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import serial
import os
import os.path
import time
import socket
import logging
import select
import errno
from serial_grabber.poster_exceptions import ConnectionException
from serial.serialutil import SerialException

SOCKET_ERRORS = [errno.EWOULDBLOCK]

if hasattr(errno, 'EDEADLOCK'):
    SOCKET_ERRORS.append(errno.EDEADLOCK)


class SerialConnection:
    """
    Base class for all serial connections.
    """

    def connect(self):
        raise NotImplementedError("connect is required")

    def read(self):
        """
        Single byte reading method
        """
        raise NotImplementedError("read is required")

    def write(self, data):
        """
        Writes data to the serial connection
        """
        raise NotImplementedError("write is required")

    def close(self):
        """
        Closes the connection.
        """
        raise NotImplementedError("close is required")

    def is_connected(self):
        """
        Returns whether the serial connection is currently open
        """
        raise NotImplementedError("is_connected is required")

    def inWaiting(self):
        """
        This method returns the numbering of bytes in the incoming buffer.
        It is required by the XBee module, as it is normally provided by
        pySerial
        """
        raise NotImplementedError("inWaiting is required")


class SerialPort(SerialConnection):
    def __init__(self, port, baud, timeout=60, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE):
        """
        :param str port: The serial port to use, eg: /dev/ttyUSB0
        :param int baud: The baud rate to use, eg: 115200
        :param int timeout: eg: 60
        :param int parity: eg: serial.PARITY_NONE
        :param int stop_bits: eg: serial.STOPBITS_ONE
        """
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.parity = parity
        self.stop_bits = stop_bits
        self.con = None

    def connect(self):
        try:
            self.con = serial.Serial(self.port, self.baud,
                                     timeout=self.timeout,
                                     parity=self.parity,
                                     stopbits=self.stop_bits)
        except OSError, e:
            time.sleep(2)
            raise ConnectionException("Port: " + self.port + " does not exists.", e)

        # These are not the droids you are looking for....
        os.system("/bin/stty -F %s %s" % (self.port, self.baud))

    def is_connected(self):
        return self.con is not None and self.con.isOpen()

    def close(self):
        if self.con is not None:
            self.con.close()
            self.con = None

    def write(self, data):
        if self.con is None:
            raise ValueError("There is no currently open connection")
        self.con.write(data)

    def read(self, size=1):
        try:
            return self.con.read(size=size)
        except SerialException, se:
            self.close()
            raise se

    def inWaiting(self):
        return self.con.inWaiting()


class TcpConnection(SerialConnection):
    """
    A TCP socket server that accepts a single connection. This is mainly
    used for development.
    """
    logger = logging.getLogger("TcpConnection")

    def __init__(self, hostname, port):
        """
        :param str hostname: The hostname to listen on
        :param int port: The port to listen on
        """
        self.hostname = hostname
        self.port = port
        self.con = None

    def is_connected(self):
        return self.con is not None

    def close(self):
        self.logger.info("Closing connection")
        if self.con is not None:
            self.con.close()
            self.con = None

    def read(self):
        """
        Read from the TCP connection, but but make sure to always return
        a non None value
        """
        try:
            c = self.con.recv(1024)
            return c
        except socket.error as e:
            if e.errno in SOCKET_ERRORS:
                return ''
            raise e

    def write(self, data):
        self.con.sendall(data)

    def inWaiting(self):
        readers, _, _ = select.select([self.con], [], [], 0)
        if len(readers) > 0:
            return 1
        else:
            return 0


class TcpServer(TcpConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(30)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.hostname, self.port))
        self.logger.info("Waiting for connection on %s:%d" %
                         (self.hostname, self.port))
        self.sock.listen(0)
        clientsocket, address = self.sock.accept()
        self.logger.info("Connection from %s" % str(address))
        self.con = clientsocket
        self.con.setblocking(False)


class TcpClient(TcpConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(30)
        self.sock.connect((self.hostname, self.port))
        self.sock.setblocking(False)
        self.con = self.sock
