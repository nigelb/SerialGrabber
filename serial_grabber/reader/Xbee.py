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
import SerialGrabber_Settings
import time
from serial_grabber import cache
from serial_grabber.reader.SerialReader import SerialReader
from serial_grabber.state import format_data
from serial_grabber.util import config_helper, get_millis
from serial import SerialException
from xbee import XBee


packet_start_byte = 0x7E
escape_marker = 0x7D


class XbeeAPIm2Reader(SerialReader):

    def run(self):
        config = config_helper({})
        config.counter = self.counter
        start = get_millis()
        dat = []
        while self.isRunning.running:
            try:
                if self.stream is None:
                    self.setup()
                    start = get_millis()
                    continue
                read_data = ""
                current = None


                #"if 0x7E is received at any time it can be assumed that a new packet has started regardless of length"
                # http://www.digi.com/support/kbase/kbaseresultdetl?id=2199

                while self.isRunning.running and ord(current) != packet_start_byte:
                    current = self.read()
                    dat.append(current)
                read_data = "".join(dat[:-1])

                if current is not None:
                    dat = [current]

                if (get_millis() - start)  <= SerialGrabber_Settings.startup_ignore_threshold_milliseconds:
                    self.logger.warn("Dropping data received inside startup threshold.")
                    continue

                if not ord(dat[0]) != packet_start_byte:
                    self.logger.error("There was unmatched input: %s"%read_data)
                else:
                    cache.cache(cache.make_payload(format_data(read_data)))
                    config.counter.read()
                    config.counter.update()

            except SerialException, se:
                self.close()
                return
            except Exception, e:
                self.counter.error()
                import traceback
                traceback.print_exc()
            if self.stream is None: time.sleep(SerialGrabber_Settings.reader_error_sleep)

    def read(self):
        """
        Reads a XBEE API Mode 2 stream and un-escapes it.
        """
        data = self.stream.read()
        if ord(data) == escape_marker:
            data = chr(0x20 ^ ord(self.stream.read()))
        return data

class XBeeReader(SerialReader):
    # http://code.google.com/p/python-xbee/
    def run(self):
        config = config_helper({})
        config.counter = self.counter
        start = get_millis()
        dat = []
        self.xbee = None
        while self.isRunning.running:
            try:
                if self.stream is None:
                    self.setup()
                    self.xbee = XBee(self.stream)
                    start = get_millis()
                    continue
                response = self.xbee.wait_read_frame()
                if response is None:
                    self.logger.error("There was an error reading")
                else:
                    cache.cache(cache.make_payload(format_data(response)))
                    config.counter.read()
                    config.counter.update()

            except SerialException, se:
                self.close()
                return
            except Exception, e:
                self.counter.error()
                import traceback
                traceback.print_exc()
            if self.stream is None: time.sleep(SerialGrabber_Settings.reader_error_sleep)
