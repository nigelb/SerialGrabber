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


from serial_grabber.reader.SerialReader import SerialConnection
import socket
import logging


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

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(60)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.hostname, self.port))
        self.logger.info("Waiting for connection on %s:%d" %
                         (self.hostname, self.port))
        self.sock.listen(0)
        clientsocket, address = self.sock.accept()
        self.logger.info("Connection from %s" % str(address))
        self.con = clientsocket

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
            return self.con.recv(1)
        except socket.error as e:
            if e.errno == 35:
                return ''
            raise e

    def write(self, data):
        self.sock.sendall(data)
