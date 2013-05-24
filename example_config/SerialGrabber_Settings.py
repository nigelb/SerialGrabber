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

#Serial Settings
import serial
from serial_grabber.filter.CountingFilter import CountingTransactionFilter
from serial_grabber.processor import CompositeProcessor, TransformCompositeProcessor
from serial_grabber.processor.FileAppenderProcessor import FileAppenderProcessor
from serial_grabber.processor.JsonFileProcessor import JsonFileProcessor
from serial_grabber.reader.FileReader import FileReader
from serial_grabber.reader.SerialReader import SerialReader
from serial_grabber.transform.EcoFestTransform import EcoFestTransform

timeout = 1
#port = "COM4"
port = "/dev/ttyUSB0"
#port=0
baud = 57600
parity = serial.PARITY_NONE
stop_bits = 1

uploader_collision_avoidance_delay = 1
uploader_sleep = 1
watchdog_sleep = 1

reader_error_sleep = 1


reader = SerialReader(port, baud,
    timeout=timeout,
    parity=parity,
    stop_bits=stop_bits)

#reader = FileReader("test_data.txt")

processor = CompositeProcessor([
    FileAppenderProcessor("all.txt"),
    TransformCompositeProcessor(EcoFestTransform(), [
        JsonFileProcessor("every_10.json", CountingTransactionFilter(10), 720),
        JsonFileProcessor("current.json", None, 1)])
])
