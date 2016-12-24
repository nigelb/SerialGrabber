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
import os
from SerialGrabber_Storage import storage_cache
from SerialGrabber_Storage import storage_archive
import datetime
from serial import SerialException
from serial_grabber.constants import current_matcher
from serial_grabber.cache import make_payload
from serial_grabber.util import config_helper, get_millis, register_worker_signal_handler


class Reader:
    """
    The base class of Reader implementations

    :param transaction_extractor: The transaction extractor used to parse the input stream.
    :type transaction_extractor: s:py:class:`serial.grabber.reader.TransactionExtractor`
    :param int startup_ignore_threshold_milliseconds: The threshold for which data will be ignored when connecting, 0 to
        disable.
    """
    logger = logging.getLogger("Reader")

    def __init__(self, transaction_extractor, startup_ignore_threshold_milliseconds, message_verifier=None):
        self.message_verifier = message_verifier
        self.startup_ignore_threshold_milliseconds = startup_ignore_threshold_milliseconds
        self.transaction_extractor = transaction_extractor
        if transaction_extractor:
            self.transaction_extractor.set_callback(lambda stream_id, emit: self.handle_transaction(stream_id, emit))
        self.storage_cache = storage_cache

    def __call__(self, *args, **kwargs):
        try:
            self.logger.info("Reader Thread Started: %s"%os.getpid())
            self.isRunning, self.counter, self.parameters, register_signal = args
            if register_signal:
                register_worker_signal_handler(self.logger)
            self.stream = None
            self.run()
        except BaseException, e:
            self.logger.exception(e)

    def setup(self):
        raise Exception("Reader method \"setup\" not implemented.")

    def close(self):
        raise Exception("Reader method \"close\" not implemented.")

    def run(self):
        start = get_millis()
        while self.isRunning.value == 1:
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
        self.close()
        self.logger.info("Shutting Down...")

    def read_data(self):
        raise Exception("Not Implemented")

    def handle_transaction(self, stream_id, emit):
        entry = make_payload(emit)
        entry['stream_id'] = stream_id
        if self.message_verifier is not None:
            isValid, response = self.message_verifier.verify_message(emit)
        path = self.storage_cache.cache(entry)
        if isValid:
            self.counter.read()
            self.counter.update()
        else:
            storage_archive.archive(path, name="invalid")
            self.counter.invalid()
            self.counter.update()
        self.stream.write(response)
        self.logger.info("End of Transaction")

