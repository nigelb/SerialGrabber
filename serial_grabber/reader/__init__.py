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
import time
import SerialGrabber_Settings, SerialGrabber_State
from serial_grabber.util import config_helper

class Reader:
    logger = logging.getLogger("Reader")
    def __call__(self, *args, **kwargs):
        self.logger.info("Reader Thread Started.")
        self.isRunning, self.counter = args
        self.stream = None
        self.run()

    def setup(self):
        raise Exception("Reader method \"setup\" not implemented.")

    def close(self):
        raise Exception("Reader method \"close\" not implemented.")

    def run(self):
        state = config_helper({})
        config = config_helper({})
        config.counter = self.counter
        while self.isRunning.running:
            try:
                if self.stream is None:
                    self.setup()
                    continue
                read_data = self.stream.readline().strip()
                if len(read_data) == 0:
                    time.sleep(SerialGrabber_Settings.reader_error_sleep)
                    continue
                matched = False
                for matcher in SerialGrabber_State.READER_STATE:
                    m = matcher(state, config, read_data)
                    if m:
                        matched = True
                        SerialGrabber_State.READER_STATE[matcher](state, config, read_data)
                if not matched:
                    self.logger.error("There was unmatched input (in trace):")
                    self.logger.trace(read_data)
            except Exception, e:
                self.counter.error()
                self.logger.error(e)
            if self.stream is None: time.sleep(SerialGrabber_Settings.reader_error_sleep)