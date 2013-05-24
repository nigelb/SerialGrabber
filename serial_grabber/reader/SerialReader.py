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

import logging
import serial
from serial_grabber import poster_exceptions
from serial_grabber.reader import Reader

class SerialReader(Reader):
    def __init__(self, port, baud, timeout=60, parity=serial.PARITY_NONE, stop_bits=serial.STOPBITS_ONE):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.parity = parity
        self.stop_bits = stop_bits

    def connect(self):
        ser = serial.Serial(self.port, self.baud,
            timeout=self.timeout,
            parity=self.parity,
            stopbits=self.stop_bits
        )
        return ser

    def try_connect(self):
        logger = logging.getLogger("SerialConnection")
        con = None
        try:
            con = self.connect()
            if con is not None: return con
        except serial.SerialException, se:
            con = None
            logger.error(se)
            logger.error("Closing port and re-opening it.")
            try:
                if con is not None and con.isOpen():
                    con.close()
            except Exception, e:
                pass
        if con is None:
            raise poster_exceptions.ConnectionException("Could not connect to port: %s"%self.port)

    def setup(self):
        self.stream = self.try_connect()

    def close(self):
        if self.stream:
            self.stream.close()
