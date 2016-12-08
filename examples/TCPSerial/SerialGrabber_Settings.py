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

from serial_grabber.reader import TransactionExtractor
from serial_grabber.reader.SerialReader import SerialReader
from serial_grabber.connections import TcpServer
from serial_grabber.processor import LoggingProcessor

# Serial Settings
hostname = "127.0.0.1"
port = 8099

# Settings
cache_collision_avoidance_delay = 1
processor_sleep = 1
watchdog_sleep = 1

reader_error_sleep = 1

drop_carriage_return = True

transaction = TransactionExtractor("default", "BEGIN DATA", "END DATA")

tcp = TcpServer(hostname, port)

reader = SerialReader(transaction, 1000, tcp)

processor = LoggingProcessor()
