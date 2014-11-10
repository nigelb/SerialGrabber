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
        self.transaction_extractor.set_callback(lambda stream_id, emit: self.handle_transaction(stream_id, emit))


    def __call__(self, *args, **kwargs):
        self.logger.info("Reader Thread Started.")
        self.isRunning, self.counter = args
        self.stream = None
        self.run()

    def getCommandStream(self):
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
        storage_cache.cache(entry)
        self.logger.info("End of Transaction")
        self.counter.read()
        self.counter.update()

# def run(self):
    #     state = config_helper({})
    #     config = config_helper({})
    #     config.counter = self.counter
    #     start = get_millis()
    #     processor_state = SerialGrabber_State.reader_state()
    #     while self.isRunning.running:
    #         try:
    #             if self.stream is None:
    #                 self.setup()
    #                 start = get_millis()
    #                 continue
    #             read_data = ""
    #             current = None
    #             dat = []
    #             while self.isRunning.running and current != "\n":
    #                 current = self.stream.read(1)
    #                 if len(current) == 0:
    #                     time.sleep(SerialGrabber_Settings.reader_error_sleep)
    #                     continue
    #                 dat.append(current)
    #
    #             read_data = "".join(dat).strip()
    #             if self.startup_ignore_threshold_milliseconds > 0 and (get_millis() - start)  <= self.startup_ignore_threshold_milliseconds:
    #                 self.logger.warn("Dropping data received inside startup threshold.")
    #                 continue
    #             if SerialGrabber_Settings.drop_carriage_return:
    #                 read_data = read_data.replace("\r","")
    #             if len(read_data) == 0:
    #                 time.sleep(SerialGrabber_Settings.reader_error_sleep)
    #                 continue
    #             matched = False
    #             for matcher in processor_state:
    #                 m = matcher(state, config, read_data)
    #                 if m:
    #                     matched = True
    #                     state[current_matcher] = m
    #                     processor_state[matcher](state, config, read_data)
    #                     del state[current_matcher]
    #             if not matched:
    #                 self.logger.error("There was unmatched input: %s"%read_data)
    #         except SerialException, se:
    #             self.close()
    #             return
    #         except Exception, e:
    #             self.counter.error()
    #             import traceback
    #             traceback.print_exc()
    #         if self.stream is None:
    #             time.sleep(SerialGrabber_Settings.reader_error_sleep)


class TransactionExtractor:
    """
    A TransactionExtractor reads a stream and breaks it into transaction beginning at the *start_boundary* and ending at
    the *stop_boundary*. Once it has create a transaction it calls the specified *callback*

    :param str stream_id: The id of the stream that this TransactionExtractor is attached to.
    :param str start_boundary: The string that specifies the beginning of the transaction.
    :param str stop_boundary: The string that specifies the end of the transaction.
    :param callback: The function called with the contents of the transaction
    :type callback: fn(stream_id, emit) or None
    """
    def __init__(self, stream_id, start_boundary, stop_boundary, callback=None):
        self.stream_id = stream_id
        self.start_boundary = start_boundary
        self.stop_boundary = stop_boundary
        self.buffer = ""
        self.callback = callback

    def set_callback(self, callback):
        self.callback = callback

    def write(self, data):
        self.buffer += data
        start = self.buffer.find(self.start_boundary)
        if start >= 0:
            self.buffer = self.buffer[start:]
        end = self.buffer.find(self.stop_boundary, len(self.start_boundary))
        if end > 0:
            emit = self.buffer[:end + len(self.stop_boundary)]
            self.buffer = self.buffer[end + len(self.stop_boundary):]
            self.callback(self.stream_id, emit)