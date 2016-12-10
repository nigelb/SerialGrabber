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
import SerialGrabber_Settings
from SerialGrabber_Storage import storage_cache
import datetime
from serial import SerialException
from serial_grabber.constants import current_matcher
from serial_grabber.cache import make_payload
from serial_grabber.util import config_helper, get_millis


class Reader:
    """
    The base class of Reader implementations

    :param transaction_extractor: The transaction extractor used to parse the input stream.
    :type transaction_extractor: s:py:class:`serial.grabber.reader.TransactionExtractor`
    :param int startup_ignore_threshold_milliseconds: The threshold for which data will be ignored when connecting, 0 to
        disable.
    """
    logger = logging.getLogger("Reader")

    def __init__(self, transaction_extractor, startup_ignore_threshold_milliseconds):
        self.startup_ignore_threshold_milliseconds = startup_ignore_threshold_milliseconds
        self.transaction_extractor = transaction_extractor
        if transaction_extractor:
            self.transaction_extractor.set_callback(lambda stream_id, emit: self.handle_transaction(stream_id, emit))
        self.storage_cache = storage_cache

    def __call__(self, *args, **kwargs):
        self.logger.info("Reader Thread Started.")
        self.isRunning, self.counter, self.parameters = args
        self.stream = None
        self.run()

    def getCommandStream(self, stream_id="default"):
        return None

    def setup(self):
        raise Exception("Reader method \"setup\" not implemented.")

    def close(self):
        raise Exception("Reader method \"close\" not implemented.")

    def run(self):
        start = get_millis()
        while self.isRunning.running:
            try:
                if self.stream is None:
                    self.setup()
                    start = get_millis()
                    continue
                current = self.read_data()
                if len(current) == 0:
                    time.sleep(SerialGrabber_Settings.reader_error_sleep)
                    continue
                if self.startup_ignore_threshold_milliseconds > 0 and (get_millis() - start) <= self.startup_ignore_threshold_milliseconds:
                    self.logger.warn("Dropping data received inside startup threshold.")
                    continue
                if SerialGrabber_Settings.drop_carriage_return:
                    current = current.replace("\r", "")
                self.transaction_extractor.write(current)
            except Exception, e:
                self.counter.error()
                import traceback
                traceback.print_exc()
            if self.stream is None:
                time.sleep(SerialGrabber_Settings.reader_error_sleep)

    def read_data(self):
        raise Exception("Not Implemented")

    def handle_transaction(self, stream_id, emit):
        entry = make_payload(emit)
        entry['stream_id'] = stream_id
        self.storage_cache.cache(entry)
        self.logger.info("End of Transaction")
        self.counter.read()
        self.counter.update()

