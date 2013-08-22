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
from collections import OrderedDict

import logging
import time
import SerialGrabber_Settings, SerialGrabber_State
import datetime, setproctitle
from serial import SerialException
from serial_grabber.util import config_helper, get_millis

#def get_millis():
#    return time.mktime(datetime.datetime.now().timetuple()) * 1000
class Reader:
    logger = logging.getLogger("Reader")
    def __call__(self, *args, **kwargs):
        self.logger.info("Reader Thread Started.")
        self.isRunning, self.counter = args
        self.stream = None
        setproctitle.setproctitle("%s - Reader",setproctitle.getproctitle())
        self.run()

    def getCommandStream(self):
        return None

    def setup(self):
        raise Exception("Reader method \"setup\" not implemented.")

    def close(self):
        raise Exception("Reader method \"close\" not implemented.")

    def run(self):
        state = config_helper({})
        config = config_helper({})
        config.counter = self.counter
        start = get_millis()
        processor_state = SerialGrabber_State.reader_state()
        while self.isRunning.running:
            try:
                if self.stream is None:
                    self.setup()
                    start = get_millis()
                    continue
                read_data = self.stream.readline().strip()
                if (get_millis() - start)  <= SerialGrabber_Settings.startup_ignore_threshold_milliseconds:
                    self.logger.warn("Dropping data received inside startup threshold.")
                    continue
                if SerialGrabber_Settings.drop_carriage_return:
                    read_data = read_data.replace("\r","")
                if len(read_data) == 0:
                    time.sleep(SerialGrabber_Settings.reader_error_sleep)
                    continue
                matched = False
                for matcher in processor_state:
                    m = matcher(state, config, read_data)
                    if m:
                        matched = True
                        processor_state[matcher](state, config, read_data)
                if not matched:
                    self.logger.error("There was unmatched input: %s"%read_data)
            except SerialException, se:
                self.close()
                return
            except Exception, e:
                self.counter.error()
                import traceback
                traceback.print_exc()
            if self.stream is None: time.sleep(SerialGrabber_Settings.reader_error_sleep)