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
import serial, os, os.path, time
from serial_grabber import poster_exceptions
from serial_grabber.poster_exceptions import ConnectionException
from serial_grabber.reader import Reader


class _Stream:
    def __init__(self, stream):
        self.stream = stream

    def write(self, *args, **kwargs):
        return self.stream.write(*args, **kwargs)


class SerialReader(Reader):
    """
    A reader that connects to the specified serial port for its input.

    :param int startup_ignore_threshold_milliseconds: The interval that input is ignored for at startup
    :param str port: The serial port to use, eg: /dev/ttyUSB0
    :param int baud: The baud rate to use, eg: 115200
    :param int timeout: eg: 60
    :param int parity: eg: serial.PARITY_NONE
    :param int stop_bits: eg: serial.STOPBITS_ONE
    """
    def __init__(self, startup_ignore_threshold_milliseconds, port, baud, timeout=60, parity=serial.PARITY_NONE, stop_bits=serial.STOPBITS_ONE):
        Reader.__init__(self, startup_ignore_threshold_milliseconds)
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.parity = parity
        self.stop_bits = stop_bits

    def connect(self):
        try:
            ser = serial.Serial(self.port, self.baud,
                                timeout=self.timeout,
                                parity=self.parity,
                                stopbits=self.stop_bits
            )
        except OSError, e:
            time.sleep(2)
            raise ConnectionException("Port: " + self.port + " does not exists.", e)

        #These are not the droids you are looking for....
        os.system("/bin/stty -F %s %s"%(self.port, self.baud))
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
            raise poster_exceptions.ConnectionException("Could not connect to port: %s" % self.port)

    def setup(self):
        self.stream = self.try_connect()

    def close(self):
        if self.stream:
            self.stream.close()
            self.stream = None

    def getCommandStream(self):
        return _Stream(self.stream)
