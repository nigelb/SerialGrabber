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
from multiprocessing import Pipe

from serial_grabber import poster_exceptions
from serial_grabber.commander import MultiProcessParameterFactory
from serial_grabber.reader import Reader


class SerialReader(Reader, MultiProcessParameterFactory):
    """
    A reader that connects to the specified serial port for its input.

    :param transaction_extractor: The transaction extractor used to parse the input stream.
    :type transaction_extractor: :py:class:`serial.grabber.reader.TransactionExtractor`
    :param int startup_ignore_threshold_milliseconds: The interval that input is ignored for at startup
    """
    def __init__(self, transaction_extractor,
                 startup_ignore_threshold_milliseconds, serial_connection):
        Reader.__init__(self, transaction_extractor, startup_ignore_threshold_milliseconds)
        self.serial_connection = serial_connection

    def try_connect(self):
        logger = logging.getLogger("SerialConnection")
        try:
            self.serial_connection.connect()
            if self.serial_connection.is_connected():
                self.stream = self.serial_connection
                return
        except serial.SerialException, se:
            time.sleep(2)
            logger.error(se)
            logger.error("Closing port and re-opening it.")
            try:
                if self.serial_connection.is_open():
                    self.serial_connection.close()
                    self.stream = None
            except Exception, e:
                pass
        if not self.serial_connection.is_connected():
            raise poster_exceptions.ConnectionException(
                "Could not connect to port: %s" % self.port)

    def setup(self):
        if self.serial_connection.is_connected():
            self.serial_connection.close()
        self.try_connect()

    def close(self):
        self.serial_connection.close()
        self.stream = None

    def read_data(self):
        return self.stream.read()

    def populate_parameters(self, paramaters):
        paramaters.command_stream = Pipe()
        paramaters.command_type = "Serial"
