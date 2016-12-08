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

from serial_grabber.extractors import TransactionExtractor
from serial_grabber.reader.FileReader import FileReader
from serial_grabber.processor import TransformProcessor
from serial_grabber.processor.UploadProcessor import UploadProcessor
from ThingSpeakTransformer import ThingSpeakTransformer

# Serial Settings
timeout = 1
port = "/dev/ttyUSB0"
baud = 57600
parity = serial.PARITY_NONE
stop_bits = 1

# Settings
cache_collision_avoidance_delay = 1
processor_sleep = 1
watchdog_sleep = 1

reader_error_sleep = 1

drop_carriage_return = True

transaction = TransactionExtractor("default", "BEGIN SENSORS", "END SENSORS")

reader = FileReader(transaction, "ThingSpeakExample.data")

uploader = UploadProcessor("http://api.thingspeak.com/update",
                           headers={'content-type': 'application/x-www-form-urlencoded'},
                           )

processor = TransformProcessor(ThingSpeakTransformer(), uploader)
